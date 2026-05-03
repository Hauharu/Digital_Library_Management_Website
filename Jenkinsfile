pipeline {
    agent any

    stages {
        stage('Setup Python') {
            steps {
                sh '''
                apt update
                apt install -y python3 python3-pip
                '''
            }
        }

        stage('Install') {
            steps {
                sh 'pip3 install -r requirements.txt'
            }
        }

        stage('Run') {
            steps {
                sh 'python3 main.py'
            }
        }
    }
}