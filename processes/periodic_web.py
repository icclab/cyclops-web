'''
Created on Apr 9, 2014

@author:  Tea Kolevska
@contact: tea.kolevska@gmail.com
@organization: ICCLab, Zurich University of Applied Sciences
@summary: Module for the periodic pricing thread

 Copyright 2014 Zuercher Hochschule fuer Angewandte Wissenschaften
 All Rights Reserved.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

'''

from threading import Thread
import sys,os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_ui.settings")
from django.conf import settings
from main_menu.models import StackUser,PricingFunc, PriceLoop, MetersCounter,\
    Udr, PriceCdr
path=os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))
import sqlite3
from django.core import urlresolvers
from django.forms import widgets
import datetime
import time
from os_api import keystone_api
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'os_api')))
import ceilometer_api
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'processes')))
import periodic
from main_menu.views import auth_token,is_auth
from time import gmtime, strftime, strptime
from threading import Timer



def periodic_counter(self,token_id,token_metering,meters_used,meter_list,func,user,time,from_date,from_time,end_date,end_time,user_id_stack,pricing_list):
    """

    Execute the periodic counter.
    
    Args:
    token_data(string): The data received with the authentication.
      token_id(string): X-Auth-token.
      meters_used: List of the meters used in the pricing function.
      meter_list: List of the available meters.
      func: The defined pricing function.
      user: The user for whom we calculate the price.
      time: The time between every loop.
      from_date: The start date.
      from_time: The start time.
      end_date: The end date.
      end_time: The end time.
      user_id_stack: The id of the user.
      
    Returns:
      DateTime: The new start time for the next loop if the duration end is before the end time of the loop.
      
    """        
    udr,new_time=get_udr(self,token_id,token_metering,user,meters_used,meter_list,func,True,from_date,from_time,end_date,end_time,user_id_stack)
    price=pricing(self,user,meter_list,pricing_list,udr)
    return new_time

def get_delta_samples(self,token_data,token_id,user,meter):
    delta=0.0
    meter2=str(meter)
    conn = sqlite3.connect(path+'/db.sqlite3',check_same_thread=False)
    cursor = conn.execute('SELECT max(ID) FROM MAIN_MENU_METERSCOUNTER')
    last = cursor.fetchone()
    #samples =list( MetersCounter.objects.filter(user_id=user,meter_name = meter))
    #last=str(samples[-1])
    return last
        
def get_udr(self,token_id,token_metering,user,meters_used,meter_list,func,web_bool,from_date,from_time,end_date,end_time,user_id_stack):   
    conn = sqlite3.connect(path+'/db.sqlite3',check_same_thread=False)
    date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    delta_list=[None]*5
    all_stats=[] 
    total=[None]*len(meters_used)
    new_time="/"
    for i in range(len(meters_used)):
        total[i]=0
        for j in range(len(meter_list)):
            if meters_used[i]==meter_list[j]["meter-name"]:
                resource_id=meter_list[j]["resource-id"]
                q=ceilometer_api.set_query(from_date,end_date,from_time,end_time,resource_id,user_id_stack,True)
                status,stat_list=ceilometer_api.meter_statistics(meters_used[i], token_metering,token_id,meter_list,True,q=q)
                unit=meter_list[j]["meter-unit"]
                if stat_list==[]:
                    total[i]+=0
                else:
                    if meter_list[j]["meter-type"]=="cumulative":
                        total[i]+=stat_list[0]["max"]-stat_list[0]["min"]
                    if meter_list[j]["meter-type"]=="gauge":
                        t1=datetime.datetime.combine(datetime.datetime.strptime(from_date,"%Y-%m-%d").date(),datetime.datetime.strptime(from_time,"%H:%M:%S").time())
                        t2=datetime.datetime.combine(datetime.datetime.strptime(end_date,"%Y-%m-%d").date(),datetime.datetime.strptime(end_time,"%H:%M:%S").time())
                        t=t2-t1
                        time_period=t.total_seconds()
                        total[i]+=stat_list[0]["average"]*time_period
                    if meter_list[j]["meter-type"]=="delta":
                        total[i]+=stat_list[0]["sum"]
                    new_time=stat_list[0]["duration-end"]   
        conn.execute("INSERT INTO MAIN_MENU_METERSCOUNTER(METER_NAME,USER_ID_ID,COUNTER_VOLUME,UNIT,TIMESTAMP) \
            VALUES ('"+ str(meters_used[i]) +"' ,' "+ str(user)+"' ,' "+str(total[i])+"' ,' "+str(unit)+"' ,' "+str(date_time)+" ')")
        #meters_counter=MetersCounter(meter_name=meters_used[i],user_id=user,counter_volume=total[i],unit=unit ,timestamp=date_time)
        #meters_counter.save() 
        #delta=get_delta_samples(self,token_metering,token_id,user,meters_used[i])
        #delta_list[i]=delta
        for i in range(len(delta_list)):
            for j in range(len(total)):
                if i==j:
                    delta_list[i]=total[j]
    conn.execute("INSERT INTO MAIN_MENU_UDR(USER_ID_ID,TIMESTAMP,PRICING_FUNC_ID_ID,PARAM1,PARAM2,PARAM3,PARAM4,PARAM5) \
           VALUES ( '"+ str(user) +"', '"+str(date_time)+"', '"+str(func)+"', '"+ str(delta_list[0]) +"','" +str(delta_list[1]) +"','" +str(delta_list[2]) +"','" + str(delta_list[3]) +" ','"+ str(delta_list[4]) +" ')")
#    udr=Udr(user_id=user,timestamp=date_time,pricing_func_id=func, param1=delta_list[0], param2=delta_list[1], param3=delta_list[2], param4=delta_list[3], param5=delta_list[4])
#    udr.save()        
    #return udr,new_time
    conn.commit()
    conn.close()
    udr={'param1':delta_list[0],'param2':delta_list[1],'param3':delta_list[2],'param4':delta_list[3],'param5':delta_list[4]}
    return udr,new_time



def pricing(self,user,meter_list,pricing_list,udr):
    
    #func=PricingFunc.objects.get(user_id=user)
    conn = sqlite3.connect(path+'/db.sqlite3',check_same_thread=False)
    cursor=conn.execute("SELECT ID FROM MAIN_MENU_PRICINGFUNC WHERE USER_ID_ID="+str(user))
    for row in cursor:
        func_id=row[0]
     
    udr_list=[]
    udr_list.append(udr['param1'])
    udr_list.append(udr['param2'])
    udr_list.append(udr['param3'])
    udr_list.append(udr['param4'])
    udr_list.append(udr['param5'])
    for i in udr_list:
        if i==None:
            i=0
            
    k=0
    for i in range(len(pricing_list)):
        j=0
        while j<len(meter_list):
            if pricing_list[i]==meter_list[j]["meter-name"]:
                pricing_list[i]=udr_list[k]
                k+=1
            else:
                j=j+1 
            
    price=0.0 
            
    for i in range(len(pricing_list)):
        if i==0:   
            if periodic.is_number(str(pricing_list[i])):    
                price=price+float(str(pricing_list[i]))
 
        if i%2!=0:
            if pricing_list[i] in ["+","-","*","/","%"]:
                if periodic.is_number(str(pricing_list[i+1])):
                    x=float(str(pricing_list[i+1]))                             
                else:
                    break                          
                if pricing_list[i]=="+":
                    price=price+x
                if pricing_list[i]=="-": 
                    price=price-x
                if pricing_list[i]=="*":
                    price=price*x
                if pricing_list[i]=="/":
                    if x!=0:
                        price=price/x
                if pricing_list[i]=="%":
                    price=price*x/100.0
    date_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #cdr=PriceCdr(user_id=user,timestamp=date_time,pricing_func_id=func, price=price)
    #cdr.save()
    conn.execute("INSERT INTO MAIN_MENU_PRICECDR(PRICE,TIMESTAMP,USER_ID_ID,PRICING_FUNC_ID_ID) \
            VALUES ('"+ str(price) +"' ,' "+ str(date_time)+"' ,' "+str(user)+"' ,' "+str(func_id)+" ')")
    conn.commit()
    conn.close()
    print ("Price calculated. Inserted into CDR table.")
    return price



class MyThread(Thread):
    def __init__(self, username,password,domain,project,user,time_f,from_date,from_time,end_date,end_time,user_id_stack,name):
        super(MyThread, self).__init__()
        auth_uri = 'http://160.85.4.64:5000'
        conn = sqlite3.connect(path+'/db.sqlite3',check_same_thread=False)
        self.username=username
        self.password=password
        self.domain=domain
        self.project=project
        status, token_data = keystone_api.get_token_v3(auth_uri,True,username=username, password=password, domain=domain,project=project)
        self.daemon = True
        self.cancelled = False
        self.token_id=token_data["token_id"] 
        self.token_metering=token_data["metering"]
        self.user=user
        #self.user=StackUser.objects.get(id=user)       
        self.from_date=from_date
        self.from_time=from_time
        self.end_date=end_date
        self.end_time=end_time
        self.time_f=float(time_f)*3600
        #self.time_f=float(time_f)
        self.user_id_stack=user_id_stack
        status_meter_list, self.meter_list = ceilometer_api.get_meter_list(self.token_id, self.token_metering)                              
        self.pricing_list=[]
        self.meters_used=[]
        #self.func=PricingFunc.objects.get(user_id=user) 
        cursor=conn.execute("SELECT PARAM1,SIGN1,PARAM2,SIGN2,PARAM3,SIGN3,PARAM4,SIGN4,PARAM5,ID FROM MAIN_MENU_PRICINGFUNC WHERE USER_ID_ID="+str(user))
        for row in cursor:
            self.pricing_list.append(row[0])
            self.pricing_list.append(row[1])
            self.pricing_list.append(row[2])
            self.pricing_list.append(row[3])
            self.pricing_list.append(row[4])
            self.pricing_list.append(row[5])
            self.pricing_list.append(row[6])
            self.pricing_list.append(row[7])
            self.pricing_list.append(row[8])
            self.func=row[9]    
        print("Inside init thread.")
        conn.commit()
        conn.close()
        self.name=name            
        for i in range(len(self.pricing_list)):
            j=0
            while j<len(self.meter_list):
                if self.pricing_list[i]==self.meter_list[j]["meter-name"]:
                    if self.pricing_list[i] in self.meters_used:
                        continue
                    else:
                        self.meters_used.append(self.pricing_list[i])                                                                
                    break
                else:
                    j=j+1
    def run(self):
        """Overloaded Thread.run"""
        print("Inside thread run")
        while not self.cancelled:
            print ("while not cancelled")
            new_time=periodic_counter(self,self.token_id,self.token_metering,self.meters_used,self.meter_list,self.func,self.user,self.time_f,self.from_date,self.from_time,self.end_date,self.end_time,self.user_id_stack,self.pricing_list)
            if new_time=="/":
                self.from_time=self.end_time
                self.from_date=self.end_date
            else:
                new_time=new_time.split("T")
                self.from_date=new_time[0]    
                self.from_time=new_time[1]
            today = datetime.date.today()
            today.strftime("%Y-%m-%d")
            now = datetime.datetime.now()
            now=datetime.time(now.hour, now.minute, now.second)
            now.strftime("%H:%M:%S")
            self.end_date=str(today)
            self.end_time=str(now)

            time.sleep(self.time_f)

    def cancel(self):
        """End this timer thread"""
        self.cancelled = True
        

    
    def setName(self,name):
        self.name=name
        
    def getName(self):
        return self.name
        
