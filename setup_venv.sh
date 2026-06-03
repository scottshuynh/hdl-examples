# Source this script to setup Python venv

GIT_ROOT_DIR=$(git rev-parse --show-toplevel)
if [ -d "${GIT_ROOT_DIR}/venv" ]; then
    echo "Found venv. Syncing..."
    source $GIT_ROOT_DIR/venv/bin/activate
    if pip show "pip-tools" > /dev/null 2>&1; then
        pip-sync
    else
        echo "pip-tools not found. Creating a fresh venv..."
        deactivate
        python -m venv --clear $GIT_ROOT_DIR/venv
        source $GIT_ROOT_DIR/venv/bin/activate
        pip install -r $GIT_ROOT_DIR/requirements.txt
    fi
else
    echo "No venv found. Creating a fresh venv..."
    python -m venv $GIT_ROOT_DIR/venv
    source $GIT_ROOT_DIR/venv/bin/activate
    pip install -r $GIT_ROOT_DIR/requirements.txt
fi

echo "Python venv setup complete."