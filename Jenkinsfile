pipeline {
    agent {
        docker {
            image 'python:3.10'
        }
    }

    stages {
        stage('Install') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Run') {
            steps {
                sh 'python index.py'
            }
        }
    }
}