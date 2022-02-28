## Made by Lost TH@2020
import tkinter as tk
import tkinter.messagebox
import threading
from datetime import datetime
import time
import sys
import ctypes
import inspect

def create_window(): #可视化
    def window2(): 
        def exit_window2(): #窗口退出事件
            button_1.config(state='normal')
            window2.destroy()
        def start_sec():
            second=controls[10].get()
            if second.isdigit():
                start_new(int(second))
        def add(second):
            try:
                if t>time.time():
                    start_new(t-time.time()+second)
                else:
                    start_new(second)
            except:
                pass
        button_1.config(state='disabled') #防止打开多个窗口
        window2=tk.Toplevel(window) #顶级窗口
        window2.title('时间选择')
        #窗口大小和定位
        width=300
        height=500
        size=str(width)+'x'+str(height)+'+'+str((window.winfo_screenwidth()-width)//2)+'+'+str((window.winfo_screenheight()-height)//2)
        window2.geometry(size)
        window2.resizable(width=False, height=False)
        #控件定义
        controls=[]
        controls.append(tk.Label(window2,text='',font=('微软雅黑',1),width=0,height=1))
        controls.append(tk.Button(window2,text='正方陈述12分钟',font=('微软雅黑',10),height=1,width=10,command=lambda:start_new(720)))
        controls.append(tk.Button(window2,text='反方提问2分钟',font=('微软雅黑',10),height=1,width=10,command=lambda:start_new(120)))
        controls.append(tk.Button(window2,text='反方准备2分钟',font=('微软雅黑',10),height=1,width=10,command=lambda:start_new(120)))
        controls.append(tk.Button(window2,text='反方报告最多3分钟',font=('微软雅黑',10),height=1,width=10,command=lambda:start_new(180)))
        controls.append(tk.Button(window2,text='正反讨论加10分钟',font=('微软雅黑',10),height=1,width=10,command=lambda:add(600)))
        controls.append(tk.Button(window2,text='评论方提问3分钟',font=('微软雅黑',10),height=1,width=10,command=lambda:start_new(180)))
        controls.append(tk.Button(window2,text='评论方准备2分钟',font=('微软雅黑',10),height=1,width=10,command=lambda:start_new(120)))
        controls.append(tk.Button(window2,text='评论方报告4分钟',font=('微软雅黑',10),height=1,width=10,command=lambda:start_new(240)))
        controls.append(tk.Button(window2,text='正方总结1分钟',font=('微软雅黑',10),height=1,width=10,command=lambda:start_new(60)))
        controls.append(tk.Entry(window2,font=('微软雅黑',8)))
        controls.append(tk.Button(window2,text='任意秒数倒计时',font=('微软雅黑',10),height=1,width=10,command=start_sec))
        controls[0].pack(pady=1)
        for i in range(1,12):
            controls[i].pack(fill='x',padx=20,pady=5)
        window2.protocol('WM_DELETE_WINDOW',exit_window2)
        window2.mainloop()
 
    def __async_raise(thread_Id, exctype):
    #在子线程内部抛出一个异常结束线程
    #如果线程内执行的是unittest模块的测试用例， 由于unittest内部又异常捕获处理，所有这个结束线程
    #只能结束当前正常执行的unittest的测试用例， unittest的下一个测试用例会继续执行，只有结束继续
    #向unittest中添加测试用例才能使线程执行完任务，然后自动结束。
        thread_Id = ctypes.c_long(thread_Id)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_Id, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_Id, None)
            raise SystemError("PyThreadState_SEtAsyncExc failed")

    def terminator(thread):
        #结束线程
        __async_raise(thread.ident, SystemExit)
    def pa():
        while True:
            time.sleep(1)
            
    def clock(): #时间标签
        label_1=tk.Label(window,text='',font=('微软雅黑',16),width=25,height=2)
        label_1.pack()
        while True:
            dt=datetime.now()
            now_time=dt.strftime("%Y{y}%m{m}%d{d}%H{h}%M{m1}%S{s}").format(y='年', m='月', d='日',h="时",m1="分",s="秒")
            try:
                label_1.config(text=now_time)
            except:
                pass
            time.sleep(0.5)
    
    def start_new(x):
        global yt
        label_2.pack_forget()
        terminator(yt)
        y=threading.Thread(target=declock,args=[x])
        yt=y
        y.setDaemon(True) #守护线程
        y.start()
    def declock(*args): #倒计时
        global label_2
        global t
        label_2.pack(pady=85)
        totaltime=int(args[0])
        t=totaltime+time.time()+0.1
        now_unix=time.time()
        while t>=now_unix:
            m, s = divmod(t-now_unix, 60)
            h, m = divmod(m, 60)
            de_time="%d:%02d:%02d" % (h, m, s)
            try:
                label_2.config(text=de_time,fg='black')
            except:
                pass
            time.sleep(1)
            now_unix=time.time()
        label_2.config(text=de_time,fg='red')
        while True: time.sleep(1)
    
    global t,yt,label_2
        
    #主窗口创建
    global window
    window=tk.Tk()
    window.title('CUPT倒计时')
    
    #窗口大小和定位
    width=500
    height=400
    size=str(width)+'x'+str(height)+'+'+str((window.winfo_screenwidth()-width)//2)+'+'+str((window.winfo_screenheight()-height)//2)
    window.geometry(size)
    window.resizable(width=False, height=False)
    
    #多线程处理
    threads=[threading.Thread(target=clock)]
    yt=threading.Thread(target=pa)
    yt.start()
    for t in threads:
        t.setDaemon(True) #守护线程
        t.start()
    button_1=tk.Button(window,text='新计时',font=('微软雅黑',12),width=6,height=1,command=window2)
    button_1.place(relx=0.83,rely=0.87)
    label_2=tk.Label(window,text='',font=('微软雅黑',64),width=40,height=1)
    window.mainloop()

    


def main():
    create_window()


if __name__ == '__main__': main()
