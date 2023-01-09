from django.http import HttpResponse
from django.shortcuts import render,redirect
from .models import User
from django.contrib import messages
# import tkinter.messagebox
from rest_framework import viewsets
from .serializer import appSerializer
import cv2
import mediapipe as mp
import time
import math
import keyboard
# Create your views here.


U = ""

class GestureRecog:
    def __init__(self):
        h, w, c = 0, 0, 0

    # 根据手指四个关节判断手指是否伸直
    def get_angle_error(self, point_4, point_3, point_2, point_1):
        try:
            point_4_cx, point_4_cy = int(point_4.x * self.w), int(point_4.y * self.h)
            point_3_cx, point_3_cy = int(point_3.x * self.w), int(point_3.y * self.h)
            point_2_cx, point_2_cy = int(point_2.x * self.w), int(point_2.y * self.h)
            point_1_cx, point_1_cy = int(point_1.x * self.w), int(point_1.y * self.h)
            angle_1 = math.degrees(math.atan((point_3_cx - point_4_cx) / (point_3_cy - point_4_cy)))
            angle_2 = math.degrees(math.atan((point_1_cx - point_2_cx) / (point_1_cy - point_2_cy)))
            angle_error = abs(angle_1 - angle_2)
            if angle_error<12:
                is_straight = 1
            else:
                is_straight = 0
        except ZeroDivisionError as e:
            angle_error = 1000
            is_straight = 0
        return angle_error, is_straight

    @staticmethod
    def recog_six(landmark, list):
        thumb_vector_y = 0 if landmark[4].y - landmark[1].y < 0 else 1
        fore_vector_y = 0 if landmark[8].y - landmark[6].y < 0 else 1
        middle_vector_y = 0 if landmark[12].y - landmark[10].y < 0 else 1
        ring_vector_y = 0 if landmark[16].y - landmark[14].y < 0 else 1
        little_vector_y = 0 if landmark[20].y - landmark[17].y < 0 else 1
        if thumb_vector_y == little_vector_y and fore_vector_y == middle_vector_y == ring_vector_y and \
                thumb_vector_y != fore_vector_y:
            if list[0] == 1 and list[1] == 0 and list[2] == 0 \
                    and list[3] == 0 and list[4] == 1:
                gesture = "six"
                return True
        return False

    @staticmethod
    def recog_nine(landmark, list):
        if list[0]==0 and list[2]==0 and list[3]==0 and list[4]==0 and list[1]==0:
            x1 = landmark[7].x - landmark[6].x
            y1 = landmark[7].y - landmark[6].y
            x2 = landmark[6].x - landmark[5].x
            y2 = landmark[6].y - landmark[5].y
            print("================",abs(x1*x2+y2*y1))
            if abs(x1*x2+y2*y1) <= 0.05:
                gesture = "nine"
                return True
        return False

    # 根据五根手指伸直程度识别手势
    @staticmethod
    def get_gesture(input_list):
        if input_list[0]==0 and input_list[1]==1 and input_list[2]==0 \
                and input_list[3]==0 and input_list[4]==0:
            gesture = "one"
        elif input_list[0]==0 and input_list[1]==1 and input_list[2]==1 \
                and input_list[3]==0 and input_list[4]==0:
            gesture = "two"
        elif input_list[0]==0 and input_list[1]==0 and input_list[2]==1 \
                and input_list[3]==1 and input_list[4]==1:
            gesture = "three"
        elif input_list[0]==0 and input_list[1]==1 and input_list[2]==1 \
                and input_list[3]==1 and input_list[4]==0:
            gesture = "three"
        elif input_list[0]==0 and input_list[1]==1 and input_list[2]==1 \
                and input_list[3]==1 and input_list[4]==1:
            gesture = "four"
        elif input_list[0]==1 and input_list[1]==1 and input_list[2]==1 \
                and input_list[3]==1 and input_list[4]==1:
            gesture = "five"
        elif input_list[0]==1 and input_list[1]==1 and input_list[2]==1 \
                and input_list[3]==0 and input_list[4]==0:
            gesture = "seven"
        elif input_list[0]==1 and input_list[1]==1 and input_list[2]==0 \
                and input_list[3]==0 and input_list[4]==0:
            gesture = "eight"
        else:
            gesture = ""
        return gesture

    @classmethod
    def show(cls):
        cap = cv2.VideoCapture(0)  # 若需要打开文件，参数改为文件路径
        mpHands = mp.solutions.hands  # 创建手势检测模型
        hands = mpHands.Hands(static_image_mode=False,
                              max_num_hands=2,
                              min_detection_confidence=0.5,  # 置信度设为默认 0.5
                              min_tracking_confidence=0.5)

        mpDraw = mp.solutions.drawing_utils  # 绘图
        pTime = 0
        cTime = 0
        while True:
            if keyboard.is_pressed("esc"):
                cv2.destroyAllWindows()
                return redirect('http://127.0.0.1:8000/main/')
            success, img = cap.read()
            # 捕捉帧
            img = cv2.flip(img, 1)  # 图像翻转 参数为1时水平翻转
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # 检测帧中的手
            results = hands.process(imgRGB)
            if results.multi_hand_landmarks:  # multi_hand_landmarks 是一个 list, 下标参考hand_landmark.png
                for handLms in results.multi_hand_landmarks:
                    for id, lm in enumerate(handLms.landmark):
                        cls.h, cls.w, cls.c = img.shape
                        print(lm.x,lm.y)
                        cx, cy = int(lm.x*cls.w), int(lm.y*cls.h)
                        cv2.circle(img, (cx,cy), 3, (255,0,255), cv2.FILLED)
                    mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

                # 判断拇指手势方向：
                is_straight_list = []
                point_4 = handLms.landmark[4]
                point_3 = handLms.landmark[3]
                point_2 = handLms.landmark[2]
                point_1 = handLms.landmark[1]
                angle_error_1, isStraight_1 = cls.get_angle_error(cls,point_4,point_3,point_2,point_1)
                print("isStraight_1:",isStraight_1)
                is_straight_list.append(isStraight_1)

                # 判断食指手势方向：
                point_4 = handLms.landmark[8]
                point_3 = handLms.landmark[7]
                point_2 = handLms.landmark[6]
                point_1 = handLms.landmark[5]
                angle_error_2, isStraight_2 = cls.get_angle_error(cls,point_4,point_3,point_2,point_1)
                print("isStraight_2:",isStraight_2)
                is_straight_list.append(isStraight_2)

                # 判断中指手势方向：
                point_4 = handLms.landmark[12]
                point_3 = handLms.landmark[11]
                point_2 = handLms.landmark[10]
                point_1 = handLms.landmark[9]
                angle_error_3, isStraight_3 = cls.get_angle_error(cls,point_4,point_3,point_2,point_1)
                print("isStraight_3:",isStraight_3)
                is_straight_list.append(isStraight_3)

                # 判断无名指手势方向：
                point_4 = handLms.landmark[16]
                point_3 = handLms.landmark[15]
                point_2 = handLms.landmark[14]
                point_1 = handLms.landmark[13]
                angle_error_4, isStraight_4 = cls.get_angle_error(cls,point_4,point_3,point_2,point_1)
                print("isStraight_4:",isStraight_4)
                is_straight_list.append(isStraight_4)

                # 判断小指手势方向：
                point_4 = handLms.landmark[20]
                point_3 = handLms.landmark[19]
                point_2 = handLms.landmark[18]
                point_1 = handLms.landmark[17]
                angle_error_5, isStraight_5 = cls.get_angle_error(cls,point_4,point_3,point_2,point_1)
                print("isStraight_5:",isStraight_5)
                is_straight_list.append(isStraight_5)
                # 根据五根手指的伸直程度判断手势所对应的数字
                if cls.recog_six(handLms.landmark, is_straight_list):
                    gesture = "six"
                elif cls.recog_nine(handLms.landmark, is_straight_list):
                    gesture = "nine"
                else:
                    gesture = cls.get_gesture(is_straight_list)
                print("gesture:", gesture)
                cv2.putText(img, gesture, (10, 100), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)


            cTime = time.time()
            fps = 1/(cTime-pTime)
            pTime = cTime
            cv2.putText(img,str(int(fps)), (10,70), cv2.FONT_HERSHEY_PLAIN, 3, (255,0,255), 3)
            cv2.imshow("Gesture Recognition", img)
            cv2.waitKey(100)

class appViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = appSerializer

    @staticmethod
    def show_sign(req):
        return render(req, 'signin.html')
    

    @staticmethod
    def show_main(req):
        print('=====show_main=====')
        return render(req, 'main.html')

    
    @staticmethod
    def login(req):
        print('=====login=====')
        if req.method == 'POST':
            global _username, U 
            _username = req.POST['username']
            U = _username
            password = req.POST['password']
            try:
                corr_pwd = User.objects.filter(username=_username).values()[0].get('userpwd')
                if corr_pwd != password:
                    print('密码不正确')
                    messages.add_message(req, messages.INFO, 'Wrong Password')
                    return redirect('http://127.0.0.1:8000/')
            except IndexError:
                print('用户名不正确')
                # tkinter.messagebox.showinfo('提示','登用户名或密码不正确')
                messages.add_message(req, messages.INFO, 'Wrong Name')
                return redirect('http://127.0.0.1:8000/')
        return render(req, 'main.html',{'msg': '欢迎！'+_username})

    
    @classmethod
    def start(cls, req):
        if req.method == 'GET':
            print(req.GET)
            cls.mpfunc()
        return redirect('http://127.0.0.1:8000/main/')


    @staticmethod
    def mpfunc():
        guestuerecog = GestureRecog()
        guestuerecog.show()


newViewSet = appViewSet()