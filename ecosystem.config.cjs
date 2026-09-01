module.exports = {
  apps: [
    {
      name: "agenthive-backend",
      cwd: "/home/ubuntu/agenthive",
      script: "/home/ubuntu/agenthive/.venv/bin/uvicorn",
      args: "backend.app.main:app --host 0.0.0.0 --port 8000 --workers 2",
      interpreter: "none",
      env: {
        PYTHONPATH: "/home/ubuntu/agenthive",
      },
      restart_delay: 3000,
      max_restarts: 10,
    },
    {
      name: "agenthive-frontend",
      cwd: "/home/ubuntu/agenthive/frontend",
      script: "./node_modules/next/dist/bin/next",
      args: "start -p 3001",
      interpreter: "node",
      env: {
        PORT: "3001",
        NODE_ENV: "production",
      },
      restart_delay: 3000,
      max_restarts: 10,
    },
  ],
};
