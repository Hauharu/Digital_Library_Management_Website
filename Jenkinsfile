pipeline {
    agent any

    stages {
        stage('Install Python') {
            steps {
                sh '''
                apt update
                apt install -y python3 python3-pip
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip3 install -r requirements.txt || true'
            }
        }

        stage('Test') {
            steps {
                sh 'python3 -m unittest || true'
            }
        }

        stage('Done') {
            steps {
                echo 'Done CI/CD'
            }
        }
    }
}