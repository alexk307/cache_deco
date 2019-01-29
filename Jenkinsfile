pipeline {
    agent none
    stages {
        stage('Build') {
            agent {
                docker {
                    image 'python:2-alpine'
                }
            }
            steps {
                sh 'pip install virtualenv'
                sh 'virtualenv env'
                sh 'source env/bin/activate'
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Test') { 
            agent {
                docker {
                    image 'python:2-alpine' 
                }
            }
            steps {
                sh 'source env/bin/activate'
                sh './env/bin/nosetests' 
            }
        }
    }
}
