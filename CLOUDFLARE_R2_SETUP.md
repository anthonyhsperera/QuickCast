# Cloudflare R2 Setup Guide for QuickCast

This guide will walk you through setting up Cloudflare R2 storage for podcast sharing functionality.

## Why R2?

- **Free Tier**: 10GB storage/month, zero egress fees
- **Cost-Effective**: Way cheaper than S3 for downloads
- **Auto-Expiration**: Built-in lifecycle policies
- **S3-Compatible**: Uses standard boto3 library

---

## Step 1: Create Cloudflare Account

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/sign-up)
2. Sign up with your email
3. Verify your email address
4. Log in to your dashboard

---

## Step 2: Enable R2 Storage

1. In the Cloudflare dashboard, click **R2** in the left sidebar
2. If prompted, click **"Purchase R2 Plan"**
   - Select the **Free Plan** (10GB storage, unlimited egress)
   - You may need to add a payment method for verification, but won't be charged on free tier
3. Click **"Enable R2"**

---

## Step 3: Create R2 Bucket

1. Click **"Create bucket"**
2. Enter bucket name: `quickcast-podcasts` (or your preferred name)
3. Select location: **Automatic** (recommended) or choose closest to your users
4. Click **"Create bucket"**

---

## Step 4: Configure Public Access (Optional but Recommended)

For easier sharing without presigned URLs:

1. Go to your bucket settings
2. Click **"Settings"** tab
3. Under **"Public access"**, click **"Allow Access"**
4. Copy the **Public Bucket URL** - it looks like:
   ```
   https://pub-xxxxxxxxxxxxxx.r2.dev
   ```
5. Save this URL - you'll need it for `R2_PUBLIC_URL`

**Alternative**: Use presigned URLs (more secure, but links are longer)

---

## Step 5: Create API Tokens

1. Go to **R2** → **Overview** in the sidebar
2. Click **"Manage R2 API Tokens"** on the right
3. Click **"Create API token"**
4. Configure the token:
   - **Token name**: `quickcast-api-token`
   - **Permissions**:
     - ✅ **Object Read & Write**
   - **TTL**: Never expire (or set your preference)
   - **Apply to specific buckets only**: Select `quickcast-podcasts`
5. Click **"Create API Token"**
6. **IMPORTANT**: Copy and save these values immediately (you won't see them again):
   - **Access Key ID**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Secret Access Key**: `yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy`

---

## Step 6: Get Your Account ID

1. Go to **R2** → **Overview**
2. On the right side, find **"Account ID"**
3. Copy the Account ID - it looks like: `abcdef1234567890abcdef1234567890`

---

## Step 7: Configure Lifecycle Policy (3-Day Auto-Delete)

1. Go to your `quickcast-podcasts` bucket
2. Click **"Settings"** tab
3. Scroll to **"Object lifecycle rules"**
4. Click **"Add rule"**
5. Configure the rule:
   - **Rule name**: `delete-after-3-days`
   - **Action**: Delete objects
   - **After**: `3` days
   - **Apply to all objects in bucket**: ✅ Yes
6. Click **"Add rule"**

This automatically deletes podcasts after 3 days, keeping your storage free!

---

## Step 8: Add Credentials to Heroku

Now add your R2 credentials to Heroku:

### Option A: Via Heroku Dashboard

1. Go to your Heroku app dashboard
2. Click **"Settings"** tab
3. Click **"Reveal Config Vars"**
4. Add these variables:

| Key | Value |
|-----|-------|
| `R2_ACCOUNT_ID` | Your Account ID from Step 6 |
| `R2_ACCESS_KEY_ID` | Your Access Key ID from Step 5 |
| `R2_SECRET_ACCESS_KEY` | Your Secret Access Key from Step 5 |
| `R2_BUCKET_NAME` | `quickcast-podcasts` |
| `R2_PUBLIC_URL` | Your Public Bucket URL from Step 4 (or leave empty for presigned URLs) |

### Option B: Via Heroku CLI

```bash
heroku config:set R2_ACCOUNT_ID=your_account_id
heroku config:set R2_ACCESS_KEY_ID=your_access_key
heroku config:set R2_SECRET_ACCESS_KEY=your_secret_key
heroku config:set R2_BUCKET_NAME=quickcast-podcasts
heroku config:set R2_PUBLIC_URL=https://pub-xxxxxx.r2.dev
```

---

## Step 9: Local Development Setup

For local testing, add to your `.env` file:

```bash
# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your_account_id_here
R2_ACCESS_KEY_ID=your_access_key_here
R2_SECRET_ACCESS_KEY=your_secret_access_key_here
R2_BUCKET_NAME=quickcast-podcasts
R2_PUBLIC_URL=https://pub-xxxxxx.r2.dev
```

---

## Step 10: Test the Setup

After deploying your updated code:

1. Generate a podcast
2. After completion, you should see a "Share" button
3. Click share and copy the link
4. Open the link in an incognito window
5. You should see the shared podcast with player!

---

## Monitoring R2 Usage

Track your usage to stay within free tier:

1. Go to **R2** → **Overview**
2. View **Storage Usage** and **Request Metrics**
3. Free tier includes:
   - 10 GB storage
   - 1 million Class A operations (writes) per month
   - 10 million Class B operations (reads) per month
   - Zero egress fees (unlimited downloads!)

**Estimated Usage for QuickCast:**
- 100 podcasts/month × 5MB each = 500MB storage ✅
- Well within free tier limits ✅

---

## Troubleshooting

### Error: "Access Denied"
- Check that your API token has **Object Read & Write** permissions
- Verify the token is applied to the correct bucket

### Error: "Bucket not found"
- Verify `R2_BUCKET_NAME` matches your bucket name exactly
- Check that Account ID is correct

### Shared links not working
- If using public access, verify it's enabled in bucket settings
- Check `R2_PUBLIC_URL` is set correctly
- Try using presigned URLs instead (set `R2_PUBLIC_URL` to empty)

### Files not auto-deleting after 3 days
- Verify lifecycle rule is configured correctly
- Check that rule applies to "all objects"
- Note: Deletion happens daily, not exactly at 72 hours

---

## Security Best Practices

1. **Never commit credentials** to git - always use environment variables
2. **Use bucket-specific tokens** - don't give access to all buckets
3. **Enable public access only if needed** - presigned URLs are more secure
4. **Set token TTL** if you want automatic rotation
5. **Monitor usage** regularly in Cloudflare dashboard

---

## Next Steps

Once you've completed this setup:

1. Deploy your updated QuickCast code to Heroku
2. Generate a test podcast
3. Share it and verify the link works!
4. Share your QuickCast with the world! 🎙️

---

## Support

- **Cloudflare R2 Docs**: https://developers.cloudflare.com/r2/
- **R2 Pricing**: https://developers.cloudflare.com/r2/pricing/
- **QuickCast Issues**: https://github.com/anthonyhsperera/QuickCast/issues

Happy sharing! 🚀
