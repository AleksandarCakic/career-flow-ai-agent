module.exports = {
  apps: [{
    name: 'career-flow-ai-agent',
    script: 'uvicorn',
    args: 'src.main:app --host 0.0.0.0 --port 8000 --reload',
    interpreter: 'python3',
    watch: true,
    ignore_watch: [
      'node_modules',
      'logs',
      '.git',
      '*.log',
      '__pycache__',
      '.pytest_cache',
      'analysis_reports',
      '*.pyc'
    ],
    watch_options: {
      followSymlinks: false
    },
    env: {
      NODE_ENV: 'development'
    }
  }]
};