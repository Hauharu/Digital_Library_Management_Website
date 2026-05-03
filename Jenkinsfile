pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Cloning source...'
            }
        }

        stage('Setup Python (local)') {
            steps {
                sh '''
                python3 -m venv venv || true
                . venv/bin/activate
                pip install --upgrade pip
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                . venv/bin/activate
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run App') {
            steps {
                sh '''
                . venv/bin/activate
                python index.py
                '''
            }
        }
    }
}