const { spawn } = require('child_process')
const path = require('path')

const REPO_ROOT = path.join(__dirname, '..', '..')
const VENV_PYTHON = path.join(REPO_ROOT, 'backend', '.venv', 'bin', 'python')
const BACKEND_DIR = path.join(REPO_ROOT, 'backend')

let serverProcess = null

function startServer() {
  return new Promise((resolve, reject) => {
    serverProcess = spawn(
      VENV_PYTHON,
      ['-m', 'uvicorn', 'memoryforge.api.app:create_app', '--factory',
       '--host', '127.0.0.1', '--port', '9147'],
      {
        cwd: BACKEND_DIR,
        env: { ...process.env, PYTHONPATH: BACKEND_DIR },
      }
    )

    serverProcess.stdout.on('data', (data) => {
      const msg = data.toString()
      if (msg.includes('Application startup complete')) {
        resolve()
      }
    })

    serverProcess.stderr.on('data', (data) => {
      const msg = data.toString()
      if (msg.includes('Application startup complete')) {
        resolve()
      }
    })

    serverProcess.on('error', reject)
    setTimeout(resolve, 3000)
  })
}

function stopServer() {
  if (serverProcess) {
    serverProcess.kill()
    serverProcess = null
  }
}

module.exports = { startServer, stopServer }
