import pandas as pd
import requests
import cv2,os
from bs4 import BeautifulSoup
import mysql.connector
import face_recognition

data = pd.read_csv('E:/faceRe/Famous Personalities.csv')
idsearch = data["id"]
name = data["name"]
fname = []
for i in range(len(name)):
    fname.append(name[i].replace(" ","-"))
    fname[i] = "-" + fname[i]
job = data["known_for_department"]
job.unique()

listurl = {}
lo = "https://www.themoviedb.org/person/"
ve = "/images/profiles"

idx = "10000"
stt = -1
for i in idsearch:
    stt += 1
    if stt == 5:
        break
    id = str(int(idx) + stt)
    id = id[-4:]
    url = lo + str(i) + fname[stt] + ve
    listurl.update({id : url})

headers = {
    'Host': 'www.themoviedb.org',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    
}

crawlp = os.getcwd() + "/crawlPicture"

for i in listurl:
    response = requests.get(listurl[i], headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    image_tags = soup.find_all("img")
       
    # Create dir
    path = os.path.join(crawlp, i)
      
    os.mkdir(path)
    
    # Thiết lập đường dẫn
    pathDir = crawlp + "/" + i
    # Change the current working directory
    os.chdir(pathDir)
    
    for counter, image_tag in enumerate(image_tags):
        try:
            image_url = "https://www.themoviedb.org/" + image_tag['src']
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(str(counter) + '.jpg', 'wb') as f:
                    for chunk in response.iter_content(chunk_size=128):
                        f.write(chunk)
        except:
            pass

'''###############Prepare Data############'''
# Hàm cập nhật tên và ID vào CSDL
def insertOrUpdate(id, name, job):

    # Connect mysql
    mydb = mysql.connector.connect(
      host="localhost",
      user="tnhu",
      password="abc123",
      database="qluser"
    )

    mycursor = mydb.cursor()
    
    # Thực thi câu lệnh 
    insert_stmt = (
        "SELECT * FROM nguoidung where id = %(n_id)s"
    )
    
    isRecordExist=0
    mycursor.execute(insert_stmt, {'n_id': id})
    
    myresult = mycursor.fetchall()
    for row in myresult:
        isRecordExist = 1
        break     

    if isRecordExist==1:
        cmd = ("UPDATE nguoidung SET hoten = %(name)s, job = %(job)s  WHERE id= %(n_id)s")
    else:
        cmd="INSERT INTO nguoidung(id,hoten,job) Values(%(n_id)s, %(name)s, %(job)s)"

    mycursor.execute(cmd, {'n_id': id, 'name': name, 'job': job})
    mydb.commit() # Lệnh để apply thay đổi
    
data = pd.read_csv("E:/faceRe/Famous Personalities.csv")
name = data["name"]
job = data["known_for_department"]

list = {}

idx = "10000"
stt = -1
for i in range(len(name)):
    stt += 1
    if stt == 5:
        break
    id = str(int(idx) + stt)
    id = id[-4:]
    list.update({id : {"hoten" : name[i], "job" : job[i]}})
    # Đưa thông tin người vào csdl
    insertOrUpdate(id,name[i], job[i])


'''*****************Dự đoán********************'''
id=0
#set text style
fontface = cv2.FONT_HERSHEY_SIMPLEX
fontscale = 0.5
fontcolor = (0,255,0)
fontcolor1 = (0,0,255)

# Hàm lấy thông tin người dùng qua ID
def getProfile(id):
    mydb = mysql.connector.connect(
      host="localhost",
      user="tnhu",
      password="abc123",
      database="qluser"
    )

    mycursor = mydb.cursor()
    
    # Thực thi câu lệnh 
    insert_stmt = (
        "SELECT * FROM nguoidung where id = %(n_id)s"
    )
    
    mycursor.execute(insert_stmt, {'n_id': id})
    myresult = mycursor.fetchall()
    profile=None
    for row in myresult:
        profile=row

    return profile


# tạo encodelist ảnh của đối tượng đưa vào dict
dictImg = dict()
crawlp = 'E:/faceRe/crawlPicture'
for i in list:
    # Trỏ đến thư mục mong muốn
    path = crawlp+"/"+i

    imagePaths=[os.path.join(path,f) for f in os.listdir(path)] 

    sampleNum=0
    listEncodeImg = []
    
    for imgpath in imagePaths:
        img = face_recognition.load_image_file(imgpath)
# =============================================================================
#         cv2.imshow('Face',img)
#         cv2.waitKey(0)
# =============================================================================
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        listEncodeImg.append(encode)
    
    dictImg.update({i:listEncodeImg})

'''################## Face Recognizer #################'''
from kivy.app import App
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture

class KivyCamera(Image):
    def __init__(self, capture, fps, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
        self.capture = capture
        Clock.schedule_interval(self.update, 1.0 / fps)

    def update(self, dt):
        ret, frame = self.capture.read()

        imgS = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
        listFaceDis= [] #Chứa độ chính xác
        listMatches = []
        for encodeFace,faceLoc in zip(encodesCurFrame,facesCurFrame):
            for i in dictImg:
                faceDis = face_recognition.face_distance(dictImg[i], encodeFace)
                matches = face_recognition.compare_faces(dictImg[i], encodeFace)
                listFaceDis.append(min(faceDis))
                for j in range(len(faceDis)):
                    if faceDis[j] == min(faceDis):
                        break
                listMatches.append(matches[j])
        
            name = 'Unknown'
            try:
                index = listFaceDis.index(min(listFaceDis))
            
                if listFaceDis[index] < 0.50:
                    
                    idx = '10000'
                    id = str(int(idx) + index)
                    id = id[-4:]
                        
                    profile = getProfile(id)
                    name = "Name: " + str(profile[1])
                else:
                    name = 'Unknown'
            except:
                pass

            y1,x2,y2,x1 = faceLoc
            y1, x2, y2, x1 = y1*4,x2*4,y2*4,x1*4
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
            cv2.rectangle(frame,(x1,y2-35),(x2,y2),(0,255,0),cv2.FILLED)
            cv2.putText(frame,name,(x1+6,y2-6),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2)
        
        
        if ret:
            # convert it to texture
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            # display image from the texture
            self.texture = image_texture


class CamApp(App):
    def build(self):
        self.capture = cv2.VideoCapture(0)
        self.my_camera = KivyCamera(capture=self.capture, fps=30)
        return self.my_camera

    def on_stop(self):
        #without this, app will not exit even if the window is closed
        self.capture.release()


if __name__ == '__main__':
    CamApp().run()