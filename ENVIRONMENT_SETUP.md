# Environment Setup & API Keys Guide

Complete guide to set up your environment for local development and deployment.

## 📋 Quick Summary

Your repo (`b24286-ui/context-compression`) is **fully up-to-date** with Shrestha-Kumar's original plus interview documentation. Both have identical code bases with the same commit history up to April 19, 2026.

## ✅ What's Already in Your Repo

| File | Status | Purpose |
|------|--------|---------|
| **README.md** | ✅ | Professional project overview |
| **RESUME_BULLET_POINTS.md** | ✅ NEW | Interview prep + resume bullets |
| **TECHNICAL_SUMMARY.md** | ✅ NEW | Technical deep dive |
| **INTERVIEW_CHECKLIST.md** | ✅ NEW | Pre-interview preparation |
| **.env.example** | ✅ NEW | Environment template |
| **backend/requirements.txt** | ✅ | Python dependencies |

## 🔧 Environment Setup Instructions

### Step 1: Clone & Navigate
```bash
git clone https://github.com/b24286-ui/context-compression.git
cd context-compression
```

### Step 2: Create `.env` File from Template
```bash
cp .env.example .env
```

### Step 3: Fill in Required API Keys

Edit `.env` with your actual values:

```bash
nano .env  # or use your favorite editor
```

## 🔑 How to Get Each API Key

### HuggingFace Token (REQUIRED for model downloads)
```bash
# 1. Go to: https://huggingface.co/settings/tokens
# 2. Click "New token"
# 3. Select "Read" permission
# 4. Copy the token
# 5. Paste into .env:

HUGGINGFACE_TOKEN=hf_xyz123abc...
```

**Why needed?** To download Qwen2.5-1.5B model weights

### OpenAI API Key (OPTIONAL - for data generation)
```bash
# 1. Go to: https://platform.openai.com/account/api-keys
# 2. Click "Create new secret key"
# 3. Copy and paste into .env:

OPENAI_API_KEY=sk-proj-xyz123abc...
```

**Why needed?** Alternative for generating synthetic training data

### Anthropic API Key (OPTIONAL - for better data generation)
```bash
# 1. Go to: https://console.anthropic.com/account/keys
# 2. Click "Create Key"
# 3. Copy and paste into .env:

ANTHROPIC_API_KEY=sk-ant-xyz123abc...
```

**Why needed?** Generate high-quality training examples using Claude

## 🚀 Backend Setup

### Option A: Standard Setup (Development)
```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend
PYTHONPATH=. python app.py
```

Backend runs on: **http://localhost:8000**

### Option B: Docker Setup (Production)
```bash
# From root directory
docker-compose up -d

# View logs
docker-compose logs -f backend
```

## 🎨 Frontend Setup

### Terminal 2: Start Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on: **http://localhost:5173**

## 📊 Verify Setup Works

### Test Backend Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "model_loaded": true}
```

### Test Frontend
Open browser: `http://localhost:5173`

You should see the compression dashboard loading.

## 🧪 Run Benchmarks

```bash
# From root directory
PYTHONPATH=. python backend/evaluation/benchmark --mode both
```

This will show:
- Compression ratio (target: >90%)
- Inference latency (target: <100ms)
- Memory usage

## ⚙️ Environment Variable Reference

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| `HUGGINGFACE_TOKEN` | ✅ YES | Download models | `hf_abc123xyz...` |
| `MODEL_NAME` | ✅ YES | Which model to use | `Qwen/Qwen2.5-1.5B-Instruct` |
| `BACKEND_PORT` | ❌ NO | Backend port | `8000` |
| `BACKEND_URL` | ❌ NO | Backend URL | `http://localhost:8000` |
| `OPENAI_API_KEY` | ❌ NO | For data generation | `sk-proj-xyz...` |
| `ANTHROPIC_API_KEY` | ❌ NO | For data generation | `sk-ant-xyz...` |
| `DEBUG` | ❌ NO | Debug mode | `true` or `false` |

## 🔍 Troubleshooting

### "CUDA out of memory"
**Solution:** Reduce batch size in `backend/config.py`
```python
BATCH_SIZE = 4  # Reduce from 8
```

### "Model not found" error
**Solution:** Ensure HuggingFace token is valid
```bash
huggingface-cli login
# Paste token when prompted
```

### "WebSocket connection refused"
**Solution:** Backend not running
```bash
# In separate terminal:
PYTHONPATH=. python backend/app.py
```

### Port already in use
**Solution:** Kill process or change port
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in .env
BACKEND_PORT=8001
```

## 🎯 Security Best Practices

1. **Never commit `.env`** - Already in `.gitignore` ✅
2. **Never share API keys** - Keep them private
3. **Rotate keys periodically** - Delete old ones
4. **Use different keys for dev/prod**

## 📚 Next Steps

1. ✅ Set up environment
2. ✅ Get API keys
3. ✅ Start backend & frontend
4. ✅ Run benchmarks
5. ✅ For interviews: Review `RESUME_BULLET_POINTS.md`

## ❓ Common Questions

**Q: Do I need all API keys?**  
A: No. Only `HUGGINGFACE_TOKEN` is required. Others are optional for advanced features.

**Q: Can I use a different GPU?**  
A: Yes. Set `CUDA_VISIBLE_DEVICES=0` to your GPU index, or `CUDA_VISIBLE_DEVICES=0,1` for multiple GPUs.

**Q: How do I use CPU only?**  
A: Set `CUDA_VISIBLE_DEVICES=` (empty) and install CPU-only PyTorch.

**Q: Which version of Python?**  
A: Python 3.10 or higher (see README.md for exact requirements).

## ✨ Final Checklist

- [ ] Repository cloned
- [ ] `.env` file created from `.env.example`
- [ ] HuggingFace token added to `.env`
- [ ] Backend virtual environment created
- [ ] `pip install -r requirements.txt` completed
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Benchmarks run successfully
- [ ] Interview documents reviewed

---

**Ready to develop!** 🚀

Questions? Check the main README.md or create a GitHub issue.
