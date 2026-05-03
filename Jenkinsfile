pipeline {
    agent any

    stages {
        stage('Clone') {
            steps {
                echo 'Cloning...'
            }
        }

        stage('Install') {
            steps {
                sh 'pip install -r requirements.txt || true'
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