pipeline {
    agent any

    environment {
        TRIAGE_SERVICE_URL = "http://YOUR_TRIAGE_MACHINE_IP:8000/triage"
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
                script {
                    // Check results.xml actually exists before reading
                    def resultsFile = 'sample_tests/results.xml'
                    if (!fileExists(resultsFile)) {
                        echo "results.xml not found — tests may not have run. Skipping triage."
                        return
                    }

                    def results = readFile(resultsFile)

                    // Check file is not empty
                    if (results.trim().isEmpty()) {
                        echo "results.xml is empty. Skipping triage."
                        return
                    }

                    def xml = new XmlSlurper().parseText(results)
                    def failureCount = 0

                    xml.testsuite.testcase.each { testcase ->
                        def failure = testcase.failure
                        if (failure.size() > 0) {
                            failureCount++

                            def payload = groovy.json.JsonOutput.toJson([
                                test_name        : testcase.@name.toString(),
                                suite            : testcase.@classname.toString(),
                                exception_type   : "AssertionError",
                                exception_message: failure.@message.toString(),
                                stack_trace      : failure.text().toString(),
                                logs_tail        : "",
                                history          : ["PASS", "PASS", "FAIL"]
                            ])

                            echo "Triaging failure ${failureCount}: ${testcase.@name}"

                            try {
                                httpRequest(
                                    url               : env.TRIAGE_SERVICE_URL,
                                    httpMode          : 'POST',
                                    contentType       : 'APPLICATION_JSON',
                                    requestBody       : payload,
                                    validResponseCodes: '200:299',
                                    timeout           : 30
                                )
                                echo "Triage sent successfully for: ${testcase.@name}"
                            } catch (Exception e) {
                                echo "Warning: Could not reach triage service for ${testcase.@name}: ${e.message}"
                            }
                        }
                    }

                    echo "Total failures triaged: ${failureCount}"
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline done — check your triage service terminal or Slack for results'
        }
        failure {
            echo 'Pipeline failed — check the stage that failed above'
        }
    }
}
