pipeline {
    agent any

    environment {
        // Your triage service address — change this to your machine's IP
        TRIAGE_SERVICE_URL = "http://192.168.1.18:8000/triage"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/admin-jayathi/RAG_FastAPI_CLS'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    cd sample_tests
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                // Run pytest — we allow failure so Jenkins
                // continues to the triage step
                sh '''
                    cd sample_tests
                    pytest test_failures.py -v \
                        --tb=short \
                        --junit-xml=results.xml \
                        -p no:randomly \
                    || true
                '''
            }
        }

        stage('Parse and Triage Failures') {
            steps {
                script {
                    // Read the pytest XML results
                    def results = readFile('sample_tests/results.xml')

                    // Parse each failed test and send to triage service
                    def xml = new XmlSlurper().parseText(results)

                    xml.testsuite.testcase.each { testcase ->
                        def failure = testcase.failure
                        if (failure.size() > 0) {
                            def payload = groovy.json.JsonOutput.toJson([
                                test_name        : testcase.@name.toString(),
                                suite            : testcase.@classname.toString(),
                                exception_type   : "AssertionError",
                                exception_message: failure.@message.toString(),
                                stack_trace      : failure.text().toString(),
                                logs_tail        : "",
                                history          : ["PASS", "PASS", "FAIL"]
                            ])

                            echo "Sending to triage: ${testcase.@name}"

                            httpRequest(
                                url            : env.TRIAGE_SERVICE_URL,
                                httpMode       : 'POST',
                                contentType    : 'APPLICATION_JSON',
                                requestBody    : payload,
                                validResponseCodes: '200:299',
                                timeout        : 30
                            )
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline complete — check Slack for triage results'
        }
    }
}
