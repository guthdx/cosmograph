module.exports = {
  apps: [{
    name: 'cosmograph',
    script: '.venv/bin/python',
    args: '-m uvicorn cosmograph.api.main:app --host 0.0.0.0 --port 8003',
    cwd: '/home/guthdx/projects/cosmograph',
    env: {
      ENVIRONMENT: 'production',
      // ANTHROPIC_API_KEY set in .env or shell
    },
    watch: false,
    instances: 1,
    autorestart: true,
    max_memory_restart: '1G'
  }]
}
