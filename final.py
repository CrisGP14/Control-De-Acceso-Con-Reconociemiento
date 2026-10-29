import cv2
import os
import serial
import time
import mysql.connector
from datetime import datetime

con = mysql.connector.connect(host="localhost",user="root",passwd ="12345678", database="bd_segurity")
def insertar(Usuario, Entrada):
    cur =con.cursor()
    #Consulta
    sql = "INSERT INTO accesos(usuario, entrada) VALUES ('{}','{}')".format(Usuario,Entrada)
    cur.execute(sql)
    con.commit()
    cur.close()

arduino = serial.Serial('/dev/ttyACM0',9600)

dataPath = '/home/pi/Desktop/Reconocimiento/Data' #Cambia a la ruta donde hayas almacenado Data
imagePaths = os.listdir(dataPath)
print('imagePaths=',imagePaths)

face_recognizer = cv2.face.LBPHFaceRecognizer_create()


face_recognizer.read('modeloLBPHFace.xml')

cap = cv2.VideoCapture(0)

faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')

while True:
    ret,frame = cap.read()
    if ret == False: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    auxFrame = gray.copy()

    faces = faceClassif.detectMultiScale(gray,1.3,5)

    for (x,y,w,h) in faces:
        rostro = auxFrame[y:y+h,x:x+w]
        rostro = cv2.resize(rostro,(150,150),interpolation= cv2.INTER_CUBIC)
        result = face_recognizer.predict(rostro)

        cv2.putText(frame,'{}'.format(result),(x,y-5),1,1.3,(255,255,0),1,cv2.LINE_AA)
        # LBPHFace
        if result[1] < 70:
            cv2.putText(frame,'{}'.format(imagePaths[result[0]]),(x,y-25),2,1.1,(0,255,0),1,cv2.LINE_AA)
            cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)
            arduino.write(b'activar')
            insertar('{}'.format(imagePaths[result[0]]),datetime.now())
            
        else:
            cv2.putText(frame,'Desconocido',(x,y-20),2,0.8,(0,0,255),1,cv2.LINE_AA)
            cv2.rectangle(frame, (x,y),(x+w,y+h),(0,0,255),2)
            arduino.write(b'desactivar')
        time.sleep(1)
        #arduino.write(b'desactivar')
        
    width = 480
    height = 320
    dim = (width, height)
    img = cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)
    print(img.shape)
    cv2.imshow('frame',img)   
    #cv2.imshow('frame',frame)
    k = cv2.waitKey(1)
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()
