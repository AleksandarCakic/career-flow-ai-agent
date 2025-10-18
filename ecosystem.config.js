module.exports = {
  apps: [{
    name: 'career-flow-api',
    script: 'uvicorn',
    args: 'src.main:app --host 0.0.0.0 --port 8000',
    interpreter: 'python3',
    cwd: '/Users/serber/Documents/Engineering/Repositories/career-flow-ai-agent',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};