# coding = utf-8
 
from flask import Flask, render_template, request, make_response, flash, send_file
import pandas as pd
import matplotlib.pyplot as plt
import os 
from functools import wraps, update_wrapper
from datetime import datetime
from nocache import nocache
import folium
from folium.plugins import HeatMap
import io
from PIL import Image
import json
import requests
import zipfile
import menu1_fn as gg
import menu2_fn as ggpop
import menu3_fn as ggarea
import menu4_fn as ggpip



tot_num = 0

# ------------------------------
# 0. 데이터 로드, 전처리
# 지역별 민원


day_wrong = '날짜를 선택해주세요 '
day_exceed = '날짜 기간이 초과되었습니다. 2018년 12월 까지 입력바랍니다.'
nan_gu = '선택된 구가 없습니다.'
nan_dong = '선택된 동이 없습니다.'
# ------------------------------
temp_year = pd.read_excel('db_v0.7.xlsx', sheet_name='Database_1')
temp_year2 =  pd.read_excel('db_v0.7.xlsx', sheet_name='Database_4')
year_list =list(temp_year['y-m'].str[:4].unique())
year_list.sort()
mon_list= ['01','02','03','04','05','06','07','08','09','10','11','12']

aa = list(set(list(temp_year2.iloc[0].values[1:])))
year_li = []
for i in aa:
    year_li.append(str(i)[:4])

year_li.sort()




app = Flask(__name__)
app.config["SECRET_KEY"] = "ABCD"

@app.after_request
def set_response_headers(r):
    r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    r.headers['Pragma'] = 'no-cache'
    r.headers['Expires'] = '0'
    return r


 
@app.route("/")
@nocache
def home():
    s_dict = gg.get_dict()
    return render_template("menu_1.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)


################################# menu_1 인구대비악취발생분석###########################################

@app.route("/menu1")
@nocache
def menu1():
    s_dict = gg.get_dict()
    return render_template("menu_1.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)

    
@app.route("/menu1_getgraph", methods=['GET'])
@nocache 
def menu1_getgraph():
    s_dict = gg.get_dict()
    global tot_num
    area_1,area_2,time_1,time_2, option="","","","",""
    tot_num+=1
    
    file_path = 'static/image/'
    file_names = os.listdir(file_path)
    for i in file_names:
        if 'save' in i:
            file = file_path+i
            os.remove(file)
            
    file_path = 'templates/'
    file_names = os.listdir(file_path)
    for i in file_names:
        if ('map' in i) or ('df' in i) or('graph' in i) or ('save' in i):
            file = file_path+i
            os.remove(file)
            
    area_1 = request.args.getlist('area_1')
    area_2 = request.args.getlist('area_2')
    time_1_1 = request.args.get('time_1_1')
    time_1_2 = request.args.get('time_1_2')
    time_2_1 = request.args.get('time_2_1')
    time_2_2 = request.args.get('time_2_2')
    option = request.args.get('option')
   
    if '구 선택' in area_1:
        flash(nan_gu)
        return render_template("menu_1.html", dict_file = s_dict, year_list = year_list, mon_list = mon_list)
    
    elif (time_1_1 =='년도') or (time_2_1 =='년도') or (time_1_2 =='월') or (time_2_2 =='월'):
        flash(day_wrong)
        return render_template("menu_1.html", dict_file = s_dict, year_list = year_list, mon_list = mon_list)
    
    elif (int(time_1_1) > int(time_2_1)):
        flash('종료일이 시작일보다 이릅니다.')
        return render_template("menu_1.html", dict_file = s_dict, year_list = year_list, mon_list = mon_list)
    elif (int(time_1_1) == int(time_2_1)) and (int(time_1_2) > int(time_2_2)):
        flash('종료일이 시작일보다 이릅니다.')
        return render_template("menu_1.html", dict_file = s_dict, year_list = year_list, mon_list = mon_list)                                      
    else:
        time_1 = time_1_1 +'-'+time_1_2
        time_2 = time_2_1+'-'+time_2_2
              
    print(area_1, area_2, time_1, time_2, option)
    
    if option =='자료저장':
        if '서울시' in area_1:
            area_1 = gg.gu_list
        gg.get_graph_export(area_1, time_1,time_2, tot_num, area_2 )
        fantasy_zip = zipfile.ZipFile('templates/save_{}.zip'.format(tot_num), 'w')
 
        for folder, subfolders, files in os.walk('templates/'):

            for file in files:
                if (file =='df{}.xlsx'.format(tot_num)) or (file =='heatmap{}.html'.format(tot_num)) or (file == 'mappoint{}.html'.format(tot_num)):
                                                            
                    fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), 'templates/'), compress_type = zipfile.ZIP_DEFLATED)

        fantasy_zip.close()
        return send_file('templates/save_{}.zip'.format(tot_num), as_attachment=True)
        
    
    elif '서울시' in area_1:
        temp = area_1
        if option=='통계산출': 
            area_1 = gg.gu_list
            gg.get_stat_gus(area_1, time_1, time_2, tot_num)
            gg.get_graph_gus(area_1, time_1, time_2,tot_num)
            return render_template("menu_1.html",  target_area= temp, target_date1=time_1, target_date2=time_2,option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        
        elif option=='발생지점':            
           gg.get_map_point_gu(area_1[0], time_1, time_2,tot_num)
           return render_template("menu_1.html", target_area=  temp, target_date1=time_1, target_date2=time_2, option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        
        elif option=='분포도':
            gg.get_map_gu(area_1[0], time_1, time_2,tot_num)
            return render_template("menu_1.html", target_area= temp, target_date1=time_1, target_date2=time_2, option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        
        else: 
            gg.get_map_compare_gu(time_1, time_2, tot_num)
            return render_template("menu_1.html", target_area=  temp, target_date1=time_1, target_date2=time_2, option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        
    elif area_2[0]=='전체':
        if option=='통계산출':
            gg.get_graph_gus(area_1, time_1, time_2, tot_num)
            gg.get_stat_gus(area_1, time_1, time_2,tot_num)
            return render_template("menu_1.html",  target_area= area_1, target_area2=area_2, target_date1=time_1, target_date2=time_2,option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        elif option=='발생지점':
           gg.get_map_point_gu(area_1[0], time_1, time_2,tot_num)
           return render_template("menu_1.html", target_area= area_1,target_area2=area_2, target_date1=time_1, target_date2=time_2, option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        elif option=='분포도':
            gg.get_map_gu(area_1[0], time_1, time_2,tot_num)
            return render_template("menu_1.html", target_area= area_1,target_area2=area_2,target_date1=time_1, target_date2=time_2, option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        
        else: 
            gg.get_map_compare_dong(area_1[0], time_1, time_2,tot_num)
            return render_template("menu_1.html", target_area= area_1, target_area2=area_2,target_date1=time_1, target_date2=time_2, option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        
    elif area_2[0] !='전체':
        if option=='통계산출':
            gg.get_graph_dongs(area_1[0], area_2, time_1, time_2, tot_num)
            gg.get_stat_dongs(area_1[0], area_2,time_1, time_2,tot_num)
            return render_template("menu_1.html",  target_area= area_1,target_area2= area_2, target_date1=time_1, target_date2=time_2,option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        elif option=='발생지점':
           gg.get_map_point_dong(area_1[0], area_2[0],time_1, time_2,tot_num)
           return render_template("menu_1.html", target_area= area_1, target_area2=area_2, target_date1=time_1, target_date2=time_2, option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        elif option=='분포도':
            gg.get_map_dong( area_1[0], area_2[0],time_1, time_2,tot_num)
            return render_template("menu_1.html", target_area= area_1, target_area2=area_2,target_date1=time_1, target_date2=time_2, option_graph=option,dict_file = s_dict, year_list = year_list, mon_list = mon_list)
        
        elif option =='지자체별분석':
            flash('동 선택시 지도비교 옵션 사용 불가')
            return render_template("menu_1.html", dict_file = s_dict, year_list = year_list, mon_list = mon_list)
    

@app.route('/menu1_map_point')
@nocache
def map():
    global tot_num
    return render_template('mappoint{}.html'.format(tot_num))

@app.route('/menu1_map_heat')
@nocache
def map2():
    global tot_num
    return render_template('heatmap{}.html'.format(tot_num))


@app.route('/menu1_map')
@nocache
def map3():
    global tot_num
    return render_template('map_{}.html'.format(tot_num))

@app.route('/data_frame_1')
@nocache
def df_1():

    global tot_num
    return render_template('df{}.html'.format(tot_num))


@app.route('/menu_1_graph')
@nocache
def menu_1_graph():

    global tot_num
    return render_template('graph_{}.html'.format(tot_num))


@app.route('/menu_1_root')
@nocache
def menu_1_root():

    global tot_num
    return render_template('cau.html')

################################# menu_2 인구대비악취발생분석###########################################
@app.route("/menu2")
@nocache
def menu2():
    s_dict = gg.get_dict()
    return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)


@app.route('/menu2_getgraph')
@nocache
def menu2_getgraph():
    s_dict = gg.get_dict()
    global tot_num

    tot_num+=1
    

    file_path = 'templates/'
    file_names = os.listdir(file_path)
    for i in file_names:
        if ('map' in i) or ('df' in i) or('graph' in i) or ('save' in i):
            file = file_path+i
            os.remove(file)
            
    area_1 = request.args.getlist('area_1')
    area_2 = request.args.getlist('area_2')
    area_1_1 = request.args.get('area_1_1')
    time_1_1 = request.args.get('time_1_1')
    time_1_2 = request.args.get('time_1_2')
    time_2_1 = request.args.get('time_2_1')
    time_2_2 = request.args.get('time_2_2')
    option = request.args.get('option')
    option2 =request.args.get('option2')
    submit = request.args.get('submit')
    submit_2 = request.args.get('submit_2')
 
    
    if (time_1_1 =='년도') or (time_2_1 =='년도') or (time_1_2 =='월') or (time_2_2 =='월'):
        flash(day_wrong)
        return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
    elif (int(time_1_1) > int(time_2_1)):
        flash('종료일이 시작일보다 이릅니다.')
        return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
    elif (int(time_1_1) == int(time_2_1)) and (int(time_1_2) > int(time_2_2)):
        flash('종료일이 시작일보다 이릅니다.')
        return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)   
    
    else:
        time_1 = time_1_1+'-'+time_1_2
        time_2 = time_2_1+'-'+time_2_2
    print(area_1, area_1_1, area_2, time_1, time_2, option)
    
    if submit:
        if option == '통계분석':   
            if not area_1:
                flash(nan_gu)
                return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
            if area_1:
                temp_area=area_1
                if '서울시' in area_1:
                    area_1 = gg.gu_list
                if (len(area_1) >= 1) & ('구 선택' not in area_1):
                    ggpop.get_pop_stat_gus(area_1, time_1, time_2, tot_num)
                    ggpop.get_pop_graph_gus(area_1, time_1, time_2, tot_num)
                    return render_template("menu_2.html", target_area = temp_area, target_date1=time_1, target_date2=time_2, option_graph=option, dict_file = s_dict,  year_list = year_list, mon_list = mon_list)



        if option =='지자체별분포':
            if not area_1:
                flash(nan_gu)
                return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
            elif area_1:
                #if '서울시' in area_1:
                 #   area_1 = gg.gu_list
                if ('서울시' not in area_1) and (len(area_1) ==1):
                    flash('2개 이상의 구를 선택해주세요.')
                    return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)

                ggpop.get_map_by_gu(area_1,time_1, time_2, tot_num)
                return render_template("menu_2.html",target_area=area_1, target_date1=time_1, target_date2=time_2,option_graph=option, dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
        
        
        if option =='화일출력':
            if not area_1:
                flash(nan_gu)
                return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
            else:
                ggpop.get_pop_export(area_1,None,None,time_1,time_2, tot_num )
                fantasy_zip = zipfile.ZipFile('templates/save_{}.zip'.format(tot_num), 'w')

                for folder, subfolders, files in os.walk('templates/'):

                    for file in files:
                        if (file =='df{}.xlsx'.format(tot_num)) or (file =='map_{}.html'.format(tot_num)) :
                             fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), 'templates/'), compress_type = zipfile.ZIP_DEFLATED)

                fantasy_zip.close()
                return send_file('templates/save_{}.zip'.format(tot_num), as_attachment=True)

        
    elif submit_2:
                           
        if option2 == '통계분석':
            if not area_2:
                flash(nan_dong)
                return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
            elif area_1_1:
                temp_area= area_2
                if '전체' in area_2:
                    area_2 = list(gg.seoul_dict[area_1_1])
                    area_2.remove('전체')
                    print(area_2)
                    
                if (len(area_2) >= 1) & ('동 선택' not in area_2):
                    ggpop.get_pop_stat_dongs(area_1_1, area_2, time_1, time_2, tot_num)
                    ggpop.get_pop_graph_dongs(area_1_1, area_2, time_1, time_2, tot_num)
                    return render_template("menu_2.html", target_area = area_1_1,target_area2 = temp_area,target_date1=time_1,target_date2=time_2,option_graph2=option2, dict_file = s_dict,  year_list = year_list, mon_list = mon_list) 



        if option2 =='지자체별분포':
            if not area_1_1:
                flash(nan_gu)
                return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
            else:
                if not area_2:
                    flash(nan_dong)
                    return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
                elif ('전체' not in area_2) and (len(area_2) ==1):
                    flash('2개 이상의 동을 선택해주세요.')
                    return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
                else:
                    ggpop.get_map_by_dong(area_1_1,area_2, time_1, time_2, tot_num)
                    return render_template("menu_2.html", target_area = area_1_1, target_area2 = area_2, target_date1=time_1, target_date2=time_2,option_graph2=option2, dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
      
        if option2 =='화일출력':
            if not area_1_1:
                flash(nan_gu)
                return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
            elif not area_2:
                flash(nan_dong)
                return render_template("menu_2.html", dict_file = s_dict,  year_list = year_list, mon_list = mon_list)
            else:
                ggpop.get_pop_export(None,area_1_1,area_2,time_1,time_2, tot_num )
                fantasy_zip = zipfile.ZipFile('templates/save_{}.zip'.format(tot_num), 'w')

                for folder, subfolders, files in os.walk('templates/'):

                    for file in files:
                        if (file =='df{}.xlsx'.format(tot_num)) or (file =='map_{}.html'.format(tot_num)) :
                             fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), 'templates/'), compress_type = zipfile.ZIP_DEFLATED)

                fantasy_zip.close()
                return send_file('templates/save_{}.zip'.format(tot_num), as_attachment=True)
                
            
    
         
                                      
        
 
            
  

@app.route('/data_frame_2')
@nocache
def df_2():

    global tot_num
    return render_template('df{}.html'.format(tot_num))

@app.route('/data_frame_2_sum')
@nocache
def df_2_sum():

    global tot_num
    return render_template('df_sum{}.html'.format(tot_num))

@app.route('/menu_2_map')
@nocache
def menu_2_map():

    global tot_num
    return render_template('map_{}.html'.format(tot_num))


@app.route('/menu_2_graph')
@nocache
def menu_2_graph():

    global tot_num
    return render_template('graph_{}.html'.format(tot_num))

@app.route('/menu_2_root')
@nocache
def menu_2_root():

    global tot_num
    return render_template('cau.html')


##################################메뉴3###############################################
@app.route("/menu3")
@nocache
def menu3():
    s_dict = gg.get_dict()
    df_area_year = list(ggarea.df_area.columns[2:])
    df_area_year.sort()
    return render_template("menu_3.html", dict_file = s_dict,year_list = df_area_year, mon_list = mon_list)

@app.route("/menu3_getgraph")
@nocache
def menu3_getgraph():
    s_dict = gg.get_dict()
    global tot_num
    df_area_year = list(ggarea.df_area.columns[2:])
    df_area_year.sort()

    tot_num+=1
    

    file_path = 'templates/'
    file_names = os.listdir(file_path)
    for i in file_names:
        if ('map' in i) or ('df' in i) or('graph' in i) or ('save' in i):
            file = file_path+i
            os.remove(file)
            
    area_1 = request.args.getlist('area_1')
    area_2 = request.args.getlist('area_2')
    area_1_1 = request.args.get('area_1_1')
    time_1_1 = request.args.get('time_1_1')
    time_1_2 = request.args.get('time_1_2')
    time_2_1 = request.args.get('time_2_1')
    time_2_2 = request.args.get('time_2_2')
    option = request.args.get('option')
    option2 =request.args.get('option2')
    submit = request.args.get('submit')
    submit_2 = request.args.get('submit_2')
    if (time_1_1 =='년도') or (time_2_1 =='년도') or (time_1_2 =='월') or (time_2_2 =='월'):
        flash(day_wrong)
        return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
    elif (int(time_1_1) > int(time_2_1)):
        flash('종료일이 시작일보다 이릅니다.')
        return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
    elif (int(time_1_1) == int(time_2_1)) and (int(time_1_2) > int(time_2_2)):
        flash('종료일이 시작일보다 이릅니다.')
        return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
    else:
        time_1 = time_1_1+'-'+time_1_2
        time_2 = time_2_1+'-'+time_2_2
    print(area_1, area_1_1, area_2, time_1, time_2, option)
    
    if submit:
        if option == '통계분석':   
            if not area_1:
                flash(nan_gu)
                return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
            if area_1:
                temp_area= area_1
                if '서울시' in area_1:
                    area_1 = gg.gu_list
                if (len(area_1) >= 1) & ('구 선택' not in area_1):
                    ggarea.get_area_stat_gus(area_1, time_1, time_2, tot_num)
                    ggarea.get_area_graph_gus(area_1, time_1, time_2, tot_num)
                    return render_template("menu_3.html", target_area = temp_area, target_date1=time_1, target_date2=time_2, option_graph=option, dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)



        if option =='지자체별분포':
            if not area_1:
                flash(nan_gu)
                return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
            elif area_1:
                #if '서울시' in area_1:
                 #   area_1 = gg.gu_list
                if ('서울시' not in area_1) and (len(area_1) ==1):
                    flash('2개 이상의 구를 선택해주세요.')
                    return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
                ggarea.get_area_map_by_gu(area_1,time_1, time_2, tot_num)
                return render_template("menu_3.html", target_area=area_1,target_date1=time_1, target_date2=time_2,option_graph=option, dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
        
        
        if option =='화일출력':
            if not area_1:
                flash(nan_gu)
                return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
            else:
                ggarea.get_area_export(area_1,None,None,time_1,time_2, tot_num )
                fantasy_zip = zipfile.ZipFile('templates/save_{}.zip'.format(tot_num), 'w')

                for folder, subfolders, files in os.walk('templates/'):

                    for file in files:
                        if (file =='df{}.xlsx'.format(tot_num)) or (file =='map_{}.html'.format(tot_num)) :
                             fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), 'templates/'), compress_type = zipfile.ZIP_DEFLATED)

                fantasy_zip.close()
                return send_file('templates/save_{}.zip'.format(tot_num), as_attachment=True)

        
    elif submit_2:
                           
        if option2 == '통계분석':
            if not area_2:
                flash(nan_dong)
                return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
            elif area_1_1:
                temp_area=area_2
                if '전체' in area_2:
                    area_2 = list(gg.seoul_dict[area_1_1])
                    area_2.remove('전체')
                    print(area_2)
                if (len(area_2) >= 1) & ('동 선택' not in area_2):
                    ggarea.get_area_stat_dongs(area_1_1, area_2, time_1, time_2, tot_num)
                    ggarea.get_area_graph_dongs(area_1_1, area_2, time_1, time_2, tot_num)
                    return render_template("menu_3.html", target_area = area_1_1,target_area2 = temp_area,target_date1=time_1,target_date2=time_2,option_graph2=option2, dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list) 



        if option2 =='지자체별분포':
            if not area_1_1:
                flash(nan_gu)
                return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
            else:
                if not area_2:
                    flash(nan_dong)
                    return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
                elif ('전체' not in area_2) and (len(area_2) ==1):
                    flash('2개 이상의 동을 선택해주세요.')
                    return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
                else:
                    ggarea.get_area_map_by_dong(area_1_1,area_2, time_1, time_2, tot_num)
                    return render_template("menu_3.html", target_area = area_1_1, target_area2=area_2,target_date1=time_1,  target_date2=time_2,option_graph=option2, dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
      
        if option2 =='화일출력':
            if not area_1_1:
                flash(nan_gu)
                return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
            elif not area_2:
                flash(nan_dong)
                return render_template("menu_3.html", dict_file = s_dict,  year_list = df_area_year, mon_list = mon_list)
            else:
                ggarea.get_area_export(None,area_1_1,area_2,time_1,time_2, tot_num )
                fantasy_zip = zipfile.ZipFile('templates/save_{}.zip'.format(tot_num), 'w')

                for folder, subfolders, files in os.walk('templates/'):

                    for file in files:
                        if (file =='df{}.xlsx'.format(tot_num)) or (file =='map_{}.html'.format(tot_num)) :
                             fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), 'templates/'), compress_type = zipfile.ZIP_DEFLATED)

                fantasy_zip.close()
                return send_file('templates/save_{}.zip'.format(tot_num), as_attachment=True)
                                       
 
            
 
    
    
    
@app.route('/data_frame_3')
@nocache
def df_3():

    global tot_num
    return render_template('df{}.html'.format(tot_num))

@app.route('/data_frame_3_sum')
@nocache
def df_3_sum():

    global tot_num
    return render_template('df_sum{}.html'.format(tot_num))

@app.route('/menu_3_map')
@nocache
def menu_3_map():

    global tot_num
    return render_template('map_{}.html'.format(tot_num))


@app.route('/menu_3_graph')
@nocache
def menu_3_graph():

    global tot_num
    
    return render_template('graph_{}.html'.format(tot_num))

@app.route('/menu_3_root')
@nocache
def menu_3_root():

    global tot_num
    return render_template('cau.html')



##################################메뉴4###############################################


@app.route("/menu4")
@nocache
def menu4():
    s_dict = gg.get_dict()
    # year_li = year_list
    # if ('2019' in year_li) or ('2020' in year_li):
    #     year_li.pop()
    # else:  year_li = year_list
    # print(year_li)
    global  year_li
    
    return render_template("menu_4.html", dict_file = s_dict, year_list = year_li, mon_list = mon_list)


@app.route("/menu4_getgraph")
@nocache
def menu4_getgraph():
    s_dict = gg.get_dict()
    # year_li = year_list
    # if ('2019' in year_li) or ('2020' in year_li):
    #     year_li.pop()
    # else:  year_li = year_list
    # print(year_li)
    global tot_num, year_li
    area_1,area_2,time_1,time_2, option="","","","",""
    tot_num+=1
    

    file_path = 'templates/'
    file_names = os.listdir(file_path)
    for i in file_names:
        if ('map' in i) or ('df' in i) or('graph' in i) or ('save' in i):
            file = file_path+i
            os.remove(file)
            
    area_1 = request.args.getlist('area_1')
    time_1_1 = request.args.get('time_1_1')
    time_1_2 = request.args.get('time_1_2')
    time_2_1 = request.args.get('time_2_1')
    time_2_2 = request.args.get('time_2_2')
    time_3 =request.args.get('time_3')
    option = request.args.get('option')
    option_2 = request.args.get('option_2')
    submit = request.args.get('submit')
    temp=area_1
    if '서울시' in area_1:
        area_1 = ggpip.gu_list

          
    if not area_1:
        flash(nan_gu)
        return render_template("menu_4.html", dict_file = s_dict, year_list = year_li, mon_list = mon_list)
        
    print(area_1, time_1, time_2, option,  option_2, time_3)

    if submit:
        if option == 'total':
            if (time_1_1 =='년도') or (time_2_1 =='년도') or (time_1_2 =='월') or (time_2_2 =='월'):
                flash(day_wrong)
                return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
            elif (int(time_1_1) > int(time_2_1)):
                flash('종료일이 시작일보다 이릅니다.')
                return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
            elif (int(time_1_1) == int(time_2_1)) and (int(time_1_2) > int(time_2_2)):
                flash('종료일이 시작일보다 이릅니다.')
                return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
            else:
                time_1 = time_1_1+'-'+time_1_2
                time_2 = time_2_1+'-'+time_2_2
            if option_2 == '통계분석':
                ggpip.get_pipe_total_stat_gus(area_1, time_1, time_2, tot_num)
                ggpip.get_pipe_total_graph_gus(area_1, time_1, time_2, tot_num)
                return render_template("menu_4.html", target_area = temp, target_date1=time_1, target_date2=time_2,option_graph=option_2, c_option= option,  dict_file = s_dict, year_list = year_li, mon_list = mon_list)
            
            elif option_2 == '분포도':
                if (len(area_1) ==1):
                    flash('2개 이상의 구를 선택해주세요.')
                    return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)

                ggpip.get_pipe_total_map_by_gu(area_1, time_1, time_2, tot_num)
                return render_template("menu_4.html", target_area=temp,target_date1=time_1, target_date2=time_2, option_graph=option_2, c_option= option,  dict_file = s_dict, year_list = year_li, mon_list = mon_list) 
            
            elif option_2 =='자료저장':
                if (len(area_1) ==1):
                    flash('2개 이상의 구를 선택해주세요.')
                    return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
                ggpip.get_pipe_export(area_1, option, time_1, time_2, tot_num, None)
                fantasy_zip = zipfile.ZipFile('templates/save_{}.zip'.format(tot_num), 'w')

                for folder, subfolders, files in os.walk('templates/'):

                    for file in files:
                        if (file =='df{}.xlsx'.format(tot_num)) or (file =='map_{}.html'.format(tot_num)) :
                             fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), 'templates/'), compress_type = zipfile.ZIP_DEFLATED)

                fantasy_zip.close()
                return send_file('templates/save_{}.zip'.format(tot_num), as_attachment=True)
          

        elif option == 'add':
            if (time_1_1 =='년도') or (time_2_1 =='년도') or (time_1_2 =='월') or (time_2_2 =='월'):
                flash(day_wrong)
                return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
            elif (int(time_1_1) > int(time_2_1)):
                flash('종료일이 시작일보다 이릅니다.')
                return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
            elif (int(time_1_1) == int(time_2_1)) and (int(time_1_2) > int(time_2_2)):
                flash('종료일이 시작일보다 이릅니다.')
                return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
            else:
                time_1 = time_1_1+'-'+time_1_2
                time_2 = time_2_1+'-'+time_2_2
            if option_2 == '통계분석':
                ggpip.get_pipe_add_stat_gus(area_1, time_1, time_2, tot_num)
                ggpip.get_pipe_add_graph_gus(area_1, time_1, time_2, tot_num)
                return render_template("menu_4.html", target_area = temp, target_date1=time_1, target_date2=time_2,option_graph=option_2, c_option= option,  dict_file = s_dict, year_list =year_li, mon_list = mon_list)
                          
            elif option_2 == '분포도':
                if (len(area_1) ==1):
                    flash('2개 이상의 구를 선택해주세요.')
                    return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
                ggpip.get_pipe_add_map_by_gu(area_1, time_1, time_2, tot_num)
                return render_template("menu_4.html",target_area = temp, target_date1=time_1, target_date2=time_2, option_graph=option_2, c_option= option,  dict_file = s_dict, year_list = year_li, mon_list = mon_list)   
            
            elif option_2 =='자료저장':
                if (len(area_1) ==1):
                    flash('2개 이상의 구를 선택해주세요.')
                    return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
                ggpip.get_pipe_export(area_1, option, time_1, time_2, tot_num, None)
                fantasy_zip = zipfile.ZipFile('templates/save_{}.zip'.format(tot_num), 'w')

                for folder, subfolders, files in os.walk('templates/'):

                    for file in files:
                        if (file =='df{}.xlsx'.format(tot_num)) or (file =='map_{}.html'.format(tot_num)) :
                             fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), 'templates/'), compress_type = zipfile.ZIP_DEFLATED)

                fantasy_zip.close()
                return send_file('templates/save_{}.zip'.format(tot_num), as_attachment=True)
        
        
                                       
        elif option == 'total_add':
            if option_2 == '통계분석':
                ggpip.get_pipe_total_add_stat_gus(area_1, None, None, tot_num)
                ggpip.get_pipe_total_add_graph_gus(area_1, None, None,  tot_num)
                return render_template("menu_4.html", target_area = temp, option_graph=option_2, c_option= option,  dict_file = s_dict, year_list =year_li, mon_list = mon_list)
                
            
            elif option_2 =='분포도':
                if not time_3:
                    flash('년도를 선택해주세요.')
                    return render_template("menu_4.html", dict_file = s_dict, year_list = year_li, mon_list = mon_list)
                else:
                    if (len(area_1) ==1):
                        flash('2개 이상의 구를 선택해주세요.')
                        return render_template("menu_4.html", dict_file = s_dict,  year_list = year_li, mon_list = mon_list)
                    ggpip.get_pipe_total_add_map_by_gu(area_1, time_3,tot_num, None, None)
                    return render_template("menu_4.html",target_area = temp, year=time_3, year_list = year_li, mon_list = mon_list, option_graph=option_2, c_option= option,  dict_file = s_dict)
                
            elif option_2 =='자료저장':
                if not time_3:
                    flash('년도를 선택해주세요.')
                    return render_template("menu_4.html", dict_file = s_dict, year_list = year_li, mon_list = mon_list)
                else:
                    ggpip.get_pipe_export(area_1, option, None, None, tot_num, time_3)
                    fantasy_zip = zipfile.ZipFile('templates/save_{}.zip'.format(tot_num), 'w')

                    for folder, subfolders, files in os.walk('templates/'):

                        for file in files:
                            if (file =='df{}.xlsx'.format(tot_num)) or (file =='map_{}.html'.format(tot_num)) :
                                 fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), 'templates/'), compress_type = zipfile.ZIP_DEFLATED)

                    fantasy_zip.close()
                    return send_file('templates/save_{}.zip'.format(tot_num), as_attachment=True)
                                  
                
   


@app.route('/data_frame_4')
@nocache
def df_4():

    global tot_num
    return render_template('df{}.html'.format(tot_num))

@app.route('/data_frame_4_sum')
@nocache
def df_4_sum():

    global tot_num
    return render_template('df_sum{}.html'.format(tot_num))

@app.route('/menu_4_map')
@nocache
def menu_4_map():

    global tot_num
    return render_template('map_{}.html'.format(tot_num))

@app.route('/menu_4_graph')
@nocache
def menu_4_graph():

    global tot_num
    return render_template('graph_{}.html'.format(tot_num))

@app.route('/menu_4_root')
@nocache
def menu_4_root():

    global tot_num
    return render_template('cau.html')




if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True)
 