pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "ou-book-app"
        CONTAINER_NAME = "ou-book-container"
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${env.BUILD_ID} ."
                sh "docker tag ${DOCKER_IMAGE}:${env.BUILD_ID} ${DOCKER_IMAGE}:latest"
            }
        }

        stage('Deploy to Docker') {
            steps {
                script {
                    // Dừng và xóa container cũ nếu đang chạy
                    sh "docker stop ${CONTAINER_NAME} || true"
                    sh "docker rm ${CONTAINER_NAME} || true"

                    // Chạy container mới
                    sh "docker run -d --name ${CONTAINER_NAME} -p 5000:5000 ${DOCKER_IMAGE}:latest"
                }
            }
        }
    }

    post {
        success {
            echo "Triển khai thành công dự án OU BOOK!"
        }
    }
}