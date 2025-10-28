from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import threading
from datetime import datetime
import shutil

from utils.config import Config
from services.scraper import ArticleScraper
from services.llm import PodcastScriptGenerator
from services.tts import SpeechmaticsTTS
from services.audio import AudioProcessor

# Import R2Storage only if boto3 is available
try:
    from services.storage import R2Storage
    R2_IMPORT_SUCCESS = True
except ImportError as e:
    print(f"⚠️  boto3 not available, sharing feature disabled: {e}")
    R2Storage = None
    R2_IMPORT_SUCCESS = False

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please set the required environment variables in a .env file")
    exit(1)

# Initialize services
scraper = ArticleScraper()
script_generator = PodcastScriptGenerator(Config.OPENAI_API_KEY)
tts = SpeechmaticsTTS(Config.SPEECHMATICS_API_KEY)
audio_processor = AudioProcessor()

# Initialize R2 storage if configured
r2_storage = None
if R2_IMPORT_SUCCESS and Config.R2_ENABLED:
    try:
        r2_storage = R2Storage(
            account_id=Config.R2_ACCOUNT_ID,
            access_key_id=Config.R2_ACCESS_KEY_ID,
            secret_access_key=Config.R2_SECRET_ACCESS_KEY,
            bucket_name=Config.R2_BUCKET_NAME,
            public_url=Config.R2_PUBLIC_URL
        )
        print(f"✅ R2 storage enabled for sharing (bucket: {Config.R2_BUCKET_NAME})")
    except Exception as e:
        print(f"⚠️  Failed to initialize R2 storage: {e}")
        r2_storage = None
elif not R2_IMPORT_SUCCESS:
    print("⚠️  R2 storage unavailable - boto3 not installed")
else:
    print("⚠️  R2 storage not configured - sharing feature disabled")

# In-memory job storage (in production, use a database)
jobs = {}

class PodcastJob:
    """Represents a podcast generation job"""

    def __init__(self, job_id: str, url: str):
        self.job_id = job_id
        self.url = url
        self.status = "pending"  # pending, processing, completed, failed
        self.progress = 0
        self.message = "Job created"
        self.error = None
        self.output_file = None
        self.partial_output_file = None  # For progressive playback
        self.completed_segments = 0
        self.total_segments = 0
        self.metadata = {}
        self.created_at = datetime.now()
        # Sharing fields
        self.share_id = None
        self.share_url = None
        self.r2_uploaded = False

def generate_podcast(job: PodcastJob):
    """Background task to generate podcast"""
    try:
        # Update status
        job.status = "processing"
        job.progress = 10
        job.message = "Scraping article content..."

        # Step 1: Scrape the URL
        article = scraper.scrape_url(job.url)
        job.metadata['article'] = {
            'title': article['title'],
            'author': article.get('author')
        }

        # Update progress
        job.progress = 25
        job.message = "Generating podcast script..."

        # Step 2: Generate podcast script
        dialogue = script_generator.generate_podcast_script(article, target_duration=2.0)
        estimated_duration = script_generator.estimate_duration(dialogue)
        job.metadata['estimated_duration'] = estimated_duration
        job.total_segments = len(dialogue)
        job.metadata['dialogue_segments'] = job.total_segments

        # Update progress
        job.progress = 30
        job.message = f"Generating speech for {job.total_segments} segments..."

        # Step 3: Generate speech for all segments with progress callback
        job_output_dir = os.path.join(Config.OUTPUT_DIR, job.job_id)
        os.makedirs(job_output_dir, exist_ok=True)

        # Partial output for progressive playback
        partial_output_path = os.path.join(job_output_dir, f"podcast_{job.job_id}_partial.wav")
        job.partial_output_file = partial_output_path

        # Progress callback that updates job and combines audio after each batch
        def progress_callback(completed, total):
            job.completed_segments = completed
            # Calculate progress: 30% + (completed/total * 60%)
            job.progress = 30 + int((completed / total) * 60)
            job.message = f"Generated {completed}/{total} segments..."

            # Combine segments so far for progressive playback
            if completed >= 1:  # Start offering partial audio after 1 segment
                try:
                    audio_processor.combine_from_directory(job_output_dir, partial_output_path, completed)
                except Exception as e:
                    print(f"Failed to create partial audio: {e}")

        audio_segments = tts.generate_dialogue_audio(dialogue, job_output_dir, progress_callback)

        # Update progress
        job.progress = 90
        job.message = "Finalizing audio..."

        # Step 4: Final combine (already done progressively, but create final version)
        output_filename = f"podcast_{job.job_id}.wav"
        output_path = os.path.join(job_output_dir, output_filename)

        combined_metadata = audio_processor.combine_segments(audio_segments, output_path)
        job.metadata['audio'] = combined_metadata

        # Normalize the final audio
        audio_processor.normalize_audio(output_path)

        # Upload to R2 for sharing (if enabled)
        if r2_storage:
            try:
                job.progress = 95
                job.message = "Uploading for sharing..."

                upload_result = r2_storage.upload_podcast(
                    file_path=output_path,
                    metadata={
                        'title': article.get('title', 'QuickCast Podcast'),
                        'author': article.get('author'),
                        'url': job.url,
                        'duration': combined_metadata.get('duration')
                    }
                )

                job.share_id = upload_result['share_id']
                job.share_url = f"/s/{job.share_id}"
                job.r2_uploaded = True
                job.metadata['share_id'] = job.share_id
                job.metadata['share_url'] = job.share_url

                print(f"✅ Podcast uploaded to R2 for sharing: {job.share_url}")
            except Exception as e:
                print(f"⚠️  Failed to upload to R2: {e}")
                # Don't fail the job if sharing upload fails

        # Update progress
        job.progress = 100
        job.status = "completed"
        job.message = "Podcast generation completed!"
        job.output_file = output_path

        # Clean up temporary segment files
        for segment in audio_segments:
            try:
                os.remove(segment['filepath'])
            except:
                pass

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.message = f"Failed: {str(e)}"
        print(f"Job {job.job_id} failed: {e}")

@app.route('/api/generate', methods=['POST'])
def generate():
    """Create a new podcast generation job"""
    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400

    url = data['url']

    # Validate URL
    if not scraper.validate_url(url):
        return jsonify({'error': 'Invalid or inaccessible URL'}), 400

    # Create job
    job_id = str(uuid.uuid4())
    job = PodcastJob(job_id, url)
    jobs[job_id] = job

    # Start background thread
    thread = threading.Thread(target=generate_podcast, args=(job,))
    thread.daemon = True
    thread.start()

    return jsonify({
        'job_id': job_id,
        'status': job.status,
        'message': job.message
    }), 202

@app.route('/api/status/<job_id>', methods=['GET'])
def status(job_id):
    """Get the status of a podcast generation job"""
    job = jobs.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    response = {
        'job_id': job.job_id,
        'status': job.status,
        'progress': job.progress,
        'message': job.message,
        'metadata': job.metadata
    }

    if job.status == "failed":
        response['error'] = job.error

    if job.status == "completed":
        response['audio_url'] = f"/api/audio/{job_id}"
    elif job.status == "processing" and job.completed_segments >= 1:
        # Partial audio available for progressive playback
        response['partial_audio_url'] = f"/api/audio/{job_id}?partial=true"
        response['completed_segments'] = job.completed_segments
        response['total_segments'] = job.total_segments

    return jsonify(response)

@app.route('/api/audio/<job_id>', methods=['GET'])
def get_audio(job_id):
    """Download the generated podcast audio (or partial audio for progressive playback)"""
    job = jobs.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Check if partial audio is requested
    is_partial = request.args.get('partial', 'false').lower() == 'true'

    if is_partial:
        # Serve partial audio for progressive playback
        if job.status != "processing" or job.completed_segments < 1:
            return jsonify({'error': 'Partial audio not yet available'}), 400

        if not job.partial_output_file or not os.path.exists(job.partial_output_file):
            return jsonify({'error': 'Partial audio file not found'}), 404

        return send_file(
            job.partial_output_file,
            mimetype='audio/wav',
            as_attachment=False,
            download_name=f"podcast_{job_id}_partial.wav"
        )
    else:
        # Serve final audio
        if job.status != "completed":
            return jsonify({'error': 'Podcast not ready yet'}), 400

        if not job.output_file or not os.path.exists(job.output_file):
            return jsonify({'error': 'Audio file not found'}), 404

        return send_file(
            job.output_file,
            mimetype='audio/wav',
            as_attachment=False,
            download_name=f"podcast_{job_id}.wav"
        )

@app.route('/api/share/<share_id>', methods=['GET'])
def get_share_metadata(share_id):
    """Get metadata for a shared podcast"""
    if not r2_storage:
        return jsonify({'error': 'Sharing not enabled'}), 503

    try:
        metadata = r2_storage.get_file_metadata(share_id)

        if not metadata.get('exists'):
            return jsonify({'error': 'Shared podcast not found or expired'}), 404

        return jsonify(metadata)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/s/<share_id>', methods=['GET'])
def serve_share_page(share_id):
    """Serve the share page HTML"""
    share_html_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'share.html')
    if os.path.exists(share_html_path):
        return send_file(share_html_path)
    return jsonify({'error': 'Share page not found'}), 404

@app.route('/share.js', methods=['GET'])
def serve_share_js():
    """Serve the share page JavaScript"""
    js_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'share.js')
    if os.path.exists(js_path):
        return send_file(js_path, mimetype='application/javascript')
    return '', 404

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    job_list = []
    for job in jobs.values():
        job_list.append({
            'job_id': job.job_id,
            'url': job.url,
            'status': job.status,
            'progress': job.progress,
            'created_at': job.created_at.isoformat()
        })

    return jsonify({'jobs': job_list})

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def index():
    """Serve the frontend"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    if os.path.exists(frontend_path):
        return send_file(frontend_path)
    return jsonify({'message': 'Podcast API is running. Use /api/generate to create a podcast.'})

@app.route('/styles.css', methods=['GET'])
def styles():
    """Serve the CSS file"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'styles.css')
    if os.path.exists(css_path):
        return send_file(css_path, mimetype='text/css')
    return '', 404

@app.route('/app.js', methods=['GET'])
def app_js():
    """Serve the JavaScript file"""
    js_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'app.js')
    if os.path.exists(js_path):
        return send_file(js_path, mimetype='application/javascript')
    return '', 404

@app.route('/SM-Logo-Black.svg', methods=['GET'])
def logo():
    """Serve the Speechmatics logo"""
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'SM-Logo-Black.svg')
    if os.path.exists(logo_path):
        return send_file(logo_path, mimetype='image/svg+xml')
    return '', 404

@app.route('/favicon.svg', methods=['GET'])
def favicon():
    """Serve the favicon"""
    favicon_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'favicon.svg')
    if os.path.exists(favicon_path):
        return send_file(favicon_path, mimetype='image/svg+xml')
    return '', 404

@app.route('/jade-gradient.png', methods=['GET'])
def jade_gradient():
    """Serve the jade gradient background"""
    gradient_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'jade-gradient.png')
    if os.path.exists(gradient_path):
        return send_file(gradient_path, mimetype='image/png')
    return '', 404

@app.route('/jade-gradient-2.png', methods=['GET'])
def jade_gradient_2():
    """Serve the second jade gradient background"""
    gradient_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'jade-gradient-2.png')
    if os.path.exists(gradient_path):
        return send_file(gradient_path, mimetype='image/png')
    return '', 404

@app.route('/amber-gradient.png', methods=['GET'])
def amber_gradient():
    """Serve the amber gradient background"""
    gradient_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'amber-gradient.png')
    if os.path.exists(gradient_path):
        return send_file(gradient_path, mimetype='image/png')
    return '', 404

@app.route('/quickcast-logo.png', methods=['GET'])
def quickcast_logo():
    """Serve the QuickCast logo"""
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'quickcast-logo.png')
    if os.path.exists(logo_path):
        return send_file(logo_path, mimetype='image/png')
    return '', 404

if __name__ == '__main__':
    # Create output directory if it doesn't exist
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("Podcast Generator API")
    print("=" * 60)
    print(f"Server starting on http://localhost:{Config.FLASK_PORT}")
    print(f"Health check: http://localhost:{Config.FLASK_PORT}/api/health")
    print("=" * 60)

    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=(Config.FLASK_ENV == 'development')
    )
