# QuickCast Deployment Guide

## Deploy to Render

This guide will help you deploy QuickCast to Render in just a few minutes.

### Prerequisites

1. A [Render account](https://render.com) (free tier available)
2. A [GitHub account](https://github.com)
3. Your API keys:
   - OpenAI API key
   - Speechmatics API key

### Step 1: Push to GitHub

1. Create a new repository on GitHub (e.g., `quickcast`)
2. Push your code:

```bash
git add .
git commit -m "Initial commit - QuickCast ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/quickcast.git
git push -u origin main
```

### Step 2: Deploy on Render

#### Option A: Using render.yaml (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Set your environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SPEECHMATICS_API_KEY`: Your Speechmatics API key
6. Click **"Apply"**

#### Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: quickcast
   - **Runtime**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn --chdir backend --bind 0.0.0.0:$PORT app:app`
5. Add environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SPEECHMATICS_API_KEY`: Your Speechmatics API key
   - `FLASK_ENV`: production
6. Click **"Create Web Service"**

### Step 3: Wait for Deployment

Render will:
1. Install ffmpeg
2. Install Python dependencies
3. Start your application

This takes about 3-5 minutes for the first deployment.

### Step 4: Access Your App

Once deployed, Render will provide you with a URL like:
```
https://quickcast.onrender.com
```

Visit this URL to access your deployed QuickCast app!

## Important Notes

### Free Tier Limitations

- Render's free tier spins down after 15 minutes of inactivity
- First request after spin-down may take 30-60 seconds
- 750 hours/month of free usage

### Environment Variables

Never commit your `.env` file! Always set API keys in Render's dashboard:
1. Go to your service dashboard
2. Click **"Environment"** in the left sidebar
3. Add your environment variables
4. Click **"Save Changes"**

### Updating Your App

After making changes:

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

Render will automatically redeploy your app!

## Troubleshooting

### Build Fails

1. Check the build logs in Render dashboard
2. Verify `build.sh` is executable: `chmod +x build.sh`
3. Ensure all dependencies are in `backend/requirements.txt`

### App Won't Start

1. Check the application logs in Render dashboard
2. Verify environment variables are set correctly
3. Make sure `OPENAI_API_KEY` and `SPEECHMATICS_API_KEY` are configured

### Audio Generation Fails

1. Verify API keys are valid and have credits
2. Check the output directory permissions
3. Ensure ffmpeg was installed correctly (check build logs)

## Cost Estimation

- **Render Free Tier**: $0/month (limited hours)
- **OpenAI API**: ~$0.10-0.30 per podcast
- **Speechmatics TTS**: Varies by usage

## Support

For issues specific to:
- **Render deployment**: Check [Render Docs](https://render.com/docs)
- **QuickCast features**: See the main README.md

---

Happy deploying! 🚀
