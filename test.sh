flake8 ./src/
rc=$?
if [ "$rc" -ne 0 ]; then
    echo "flake8 failed, not continuing to tests"
    exit 1
fi
find ./src/ -type f -name "*.py" | xargs pylint 
rc=$?
if [ "$rc" -ne 0 ]; then
    echo "pylint failed, not continuing to tests"
    exit 1
fi