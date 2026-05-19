pipeline {
    agent any

    environment {
        TRIAGE_SERVICE_URL = "http://192.168.1.18:8000/triage"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/admin-jayathi/RAG_FastAPI_CLS.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    cd sample_tests
                    python3 -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    cd sample_tests
                    python3 -m pytest test_failures.py -v \
                        --tb=short \
                        --junit-xml=results.xml \
                    || true
                '''
            }
        }

        stage('Triage Failures') {
            steps {
                sh '''
                    # Check results file exists
                    if [ ! -f sample_tests/results.xml ]; then
                        echo "No results.xml found — skipping triage"
                        exit 0
                    fi

                    echo "Parsing failures and sending to triage service..."

                    # Use Python to parse XML and call triage service
                    # This avoids Jenkins sandbox restrictions entirely
                    python3 - <<'PYEOF'
import xml.etree.ElementTree as ET
import json
import urllib.request
import urllib.error
import os

TRIAGE_URL = os.environ.get("TRIAGE_SERVICE_URL", "http://localhost:8000/triage")

tree = ET.parse("sample_tests/results.xml")
root = tree.getroot()

# Handle both <testsuites><testsuite> and <testsuite> root formats
testcases = root.findall(".//testcase")

failure_count = 0

for testcase in testcases:
    failure_el = testcase.find("failure")
    error_el   = testcase.find("error")

    problem = failure_el if failure_el is not None else error_el
    if problem is None:
        continue

    failure_count += 1
    test_name = testcase.get("name", "unknown")
    classname  = testcase.get("classname", "unknown")
    message    = problem.get("message", "")
    stacktrace = problem.text or ""

    payload = {
        "test_name":         test_name,
        "suite":             classname,
        "exception_type":    "AssertionError",
        "exception_message": message,
        "stack_trace":       stacktrace,
        "logs_tail":         "",
        "history":           ["PASS", "PASS", "FAIL"]
    }

    print(f"\\nTriaging [{failure_count}]: {test_name}")
    print(f"  Message : {message[:120]}")

    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        TRIAGE_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(f"  Category   : {result.get('category')}")
            print(f"  Confidence : {result.get('confidence')}")
            print(f"  Owner      : {result.get('suggested_owner')}")
            print(f"  Root cause : {result.get('root_cause_summary')}")
            print(f"  Real bug   : {result.get('is_real_bug')}")
            print(f"  Rerun      : {result.get('rerun_recommended')}")
    except urllib.error.URLError as e:
        print(f"  WARNING: Could not reach triage service — {e.reason}")
        print(f"  Make sure uvicorn is running on {TRIAGE_URL}")
    except Exception as e:
        print(f"  WARNING: Unexpected error — {e}")

print(f"\\nDone. Total failures triaged: {failure_count}")
PYEOF
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline complete — check console output above for triage results'
        }
    }
}
