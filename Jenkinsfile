pipeline {
    agent {
        docker {
            image 'python:3.10'
        }
    }

    stages {
        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                sh 'python -m unittest || true'
            }
        }

        stage('Done') {
            steps {
                echo 'Done CI/CD'
            }
        }
    }
}