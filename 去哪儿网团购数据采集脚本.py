import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import json
import re
import os
import csv
import pymongo
import pymysql
import jieba.analyse

#利用用户代理、Cookie模拟登录
def request_get(network,headers):
    res = requests.get(network,headers=headers)
    time.sleep(1)
    return res

#利用selenium进行模拟用户操作
def driver_get(url):
    driver.get(url)

def driver_execute_script():
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

def get_maininfos(url):
    # 导入selenium模拟用户操作函数
    driver.get(url)
    # 利用Selenium模拟下拉操作（js）
    driver_execute_script()
    # 设置访问时间，降低访问频率
    time.sleep(10)
    # 对Selenium模拟的获得的网页源代码进行解析，便于后续xpath的使用
    dom = etree.HTML(driver.page_source)
    names = dom.xpath('//div[@class="nm"]/@title')  # 景区名称
    content = dom.xpath('//div[@class="sm"]/@title')
    bought_numbers = dom.xpath('//div[@class="tip"]/span[2]/em[1]/text()')
    networks = re.findall('<a target="_blank" href="(.*?)">', driver.page_source)
    photos_networks = dom.xpath('//div[@class="imgs loading"]/img/@data-lazy')
    money = dom.xpath('//span[@class="cash"]/em/text()')
    # 对不相关的网址进行切片处理
    del networks[30:]
    return names,content,bought_numbers,networks,photos_networks,money

#自定义对第三种团购详细页网址的信息采集函数
def get_detailinfos2(url):
    # 使用Selenium的get方法对目标网址发起请求
    driver.get(url)
    # 利用自定义的模拟下拉函数，将未加载的网址信息加载出来
    driver_execute_script()
    driver.implicitly_wait(2)#隐式等待2秒
    #经过大量实验观察得知，少量网页缺少以下某些信息，对此进行特殊处理
    try:
        advanceDayDescs = driver.find_element(by=By.CSS_SELECTOR,value='#app > div.main-flex > div.m-content > div.m-content-item.m-product-fee > div.m-content-con > div:nth-child(7) > p')# 团购的注意事项
        advanceDayDescs=advanceDayDescs.text
    except:
        advanceDayDescs='空'
    try:
        arrives = driver.find_element(by=By.CSS_SELECTOR,value='#app > div.main-flex > div.m-content > div.m-content-item.m-product_feature > div.m-product-feature.m-content-item > div.m-content-con.m-product-feature-list > div:nth-child(1) > span.value') # 团购的包含景点
        arrives = arrives.text
    except:
        arrives = '空'
    try:
        toTraffics = driver.find_element(by=By.CSS_SELECTOR,value='#m-select > div.m-select-wrap.m-select-traffic.g-flexbox > div.m-select-cont.traffics > div > p.name') # 团购的出行方式（去）
        toTraffics = toTraffics.text
    except:
        toTraffics ='空'
    backTraffics = toTraffics  # 团购的出行方式（回）
    enids = '空'  # 团购的独特ID
    try:
        travenames = driver.find_element(by=By.CSS_SELECTOR,value='#app > div.main-flex > div.m-supplier > div.g-flexbox-start > div.flex > p')  # 团购的旅游公司名称
        travenames = travenames.text
    except:
        travenames='空'
    shopnames = travenames  # 团购的发布来源
    try:
        hotelstandards = driver.find_element(by=By.CSS_SELECTOR,value='#app > div.main-flex > div.m-content > div.m-content-item.m-product_feature > div.hotel-reference > div.hotel-reference-lists > div > div.flex.cont > p.tit')  # 住宿条件
        hotelstandards = hotelstandards.text
    except:
        hotelstandards = '空'
    visitspots = '空'
    return advanceDayDescs, arrives, toTraffics, backTraffics, enids, travenames, shopnames, hotelstandards, visitspots#返回相关信息

#自定义提取静态团购详细页的网址
def get_detailinfos3_href(network,headers):
    # 发起HTTP请求
    res = requests.get(network,headers=headers)
    # 利用正则表达式提取相关信息
    detail_href_list = re.findall(r"location.href =(.*);", res.text)
    # 因为正则表达式返回的信息以列表方式存在，而列表第一个元素即为静态团购详细页网址的信息
    detail_href = detail_href_list[0]
    # 字符串处理
    href = detail_href.replace('//', 'https://').replace(' + window.location.hash', '').replace("'",'')
    # 返回处理好的静态团购详细页网址
    return href

def get_detailinfos3(network,headers):
    # 利用已经设置好的头部信息包含用户代理以及Cookie进行模拟登录
    res = requests.get(network, headers=headers)
    # 设置访问时间，降低频率
    time.sleep(3)
    html = res.text
    try:
        advanceDayDescs = re.findall('"advanceDayDesc":"(.*?)"',html)[0]
    except:
        advanceDayDescs = '空'
    try:
        arrives = re.findall('"showArrive":"(.*?)"',html)[0]
    except:
        arrives = '空'
    try:
        toTraffics = re.findall('"toTraffic":"(.*?)"',html)[0] # 团购的出行方式（去）
    except:
        toTraffics = '空'
    try:
        backTraffics = re.findall('"backTraffic":"(.*?)"',html)[0]  # 团购的出行方式（回）
    except:
        backTraffics="空"
    try:
        enids = re.findall('"enIdShow":"(.*?)"',html)[0]  # 团购的独特ID
    except:
        enids = "空"
    try:
        travenames =  re.findall("var sName = '(.*?)'",html)[0]  # 团购的旅游公司名称
    except:
        travenames = '空'
    try:
        shopnames = re.findall('<div class="name cf">.*?<em title="(.*?)">',html,re.S)[0]   # 团购的发布来源
    except:
        shopnames = "空"
    try:
        hotelstandards = re.findall('"hotelDesc":"(.*?)"',html)[0] # 住宿条件
    except:
        hotelstandards='空'
    try:
        visitspots = re.findall('"tourDesc":"(.*?)"',html)[0]
    except:
        visitspots = '空'
    return advanceDayDescs, arrives, toTraffics, backTraffics, enids, travenames, shopnames, hotelstandards, visitspots

#利用json解析，将网页文本解析成相应格式，从而提取相关评论信息
def json_infos(html):
    # 将团购详细网页源代码解析为Python字典格式
    infos = json.loads(html)
    # 提取相关上一步中对应的键的信息，并赋值为data1s
    data1s = infos["data"]["product"]
    # 提取相关上一步中对应的键的信息，并赋值为data2s
    data2s = infos["data"]["product"]["supplier"]
    try:
        advanceDayDescs = data1s['advanceDayDesc']#团购的注意事项
    except:
        advanceDayDescs="空"
    try:
        arrives = data1s['arrive']#团购的包含景点
    except:
        arrives = "空"
    try:
        toTraffics = data1s['toTraffic']#团购的出行方式（去）
    except:
        toTraffics = "空"
    backTraffics = toTraffics#团购的出行方式（回）
    try:
        enids = data1s['enId']#团购的独特ID
    except:
        enids = "空"
    try:
        travename = data2s["name"]#团购的旅游公司名称
    except:
        travename = '空'
    try:
        shopname = data2s["shopName"]#团购的发布来源
    except:
        shopname = '空'
    try:
        hotelstandard = data1s["hotelStandard"]#住宿条件
    except:
        hotelstandard = '空'
    try:
        visitspots = data1s["visitSpots"]#浏览的景点总个数
    except:
        visitspots = '空'
    return advanceDayDescs,arrives,toTraffics,backTraffics,enids,travename,shopname,hotelstandard,visitspots


#保存获取的信息函数
def save_infos(names,contents,bought_numbers,moneies,enids_list,networks,advanceDayDescs_list,arrives_list,toTraffics_list,backTraffics_list,
               travename_list,shopname_list,hotelstandard_list,visitspots_list):
    for name,content,bought_number,money,enid,network,advanceDayDesc,arrive,toTraffic,backTraffic,travename,shopname,hotelstandard,visitspot in zip\
        (names,contents,bought_numbers,moneies,enids_list,networks,advanceDayDescs_list,arrives_list,toTraffics_list,backTraffics_list,
         travename_list,shopname_list,hotelstandard_list,visitspots_list):
        Infos={"团购名称":name,
               "旅行内容":content,
               "已购人数":bought_number,
               "旅游ID":enid,
               "价格/1人":money,
               "团购网址":network,
               "注意事项":advanceDayDesc,
               "目的地景点":arrive,
               "去的方式":toTraffic,
               "回来的方式":backTraffic,
               "团购公司":travename,
               "团购发布来源":shopname,
               "住宿条件":hotelstandard,
               "浏览景点的总个数":visitspot}
        name1=name.split(' ')[0]
        network1=network.split('arrive')[0]
        fw.write(name1)
        print(Infos)
        writer.writerow(
            [name,content,bought_number,enid,money,network,advanceDayDesc,arrive,toTraffic,backTraffic,travename,shopname,hotelstandard,visitspot])
        Qunar_Infos.insert_one(Infos)
        try:
            cursor.execute(  # 写入MySQL数据库
                "insert into Qunar_Infos(团购名称,旅行内容,已购人数,旅游ID,价格每1人,团购网址,注意事项,目的地景点,去的方式,回来的方式,团购公司,团购发布来源,住宿条件,浏览景点的总个数)\
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (name,content,bought_number,enid,money,network1,advanceDayDesc,arrive,toTraffic,backTraffic,travename,shopname,hotelstandard,visitspot))
            conn.commit()
        except:
            pass
    print("数据采集完毕！")

# 利用jieba库创建词云
def jieba_creation():
    fw=open("./Qunar.txt", "r",encoding="utf-8")
    content=fw.read()
    ff=open("./Qunar_top.txt","a",encoding='utf-8')
    words=jieba.analyse.extract_tags(content,topK=15,withWeight=True)
    for word in words:
        # 计算每个词的权重，从而获得高频词
        ff.write(word[0]+'\t'+str(int(word[1]*1000))+'\n')
    fw.close()
    ff.close()





def get_infos(page,paragraph):
    a = 1
    for i in range(0,page*30,30):
        print("正在爬取第",paragraph,"页")
        save_path = 'E://pycharm试用/23到24学年上学期/网络爬虫/网络爬虫大作业之去哪儿旅行/photos5/'
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        url='https://tuan.qunar.com/vc/index.php?category=travel_d&limit={}%2C30'.format(str(i))#需要询问的网址页数

        names, contents, bought_numbers, networks,photos_networks,moneies= get_maininfos(url)
        if len(photos_networks) != 0:
            for photos_network,name in zip(photos_networks,names):
                headers1 = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
                    'Cookie': 'SECKEY_ABVK=bB/KvL9gpm3FvU8naxGvLrv/CY4rej1YNLvBCqB7b8k%3D; BMAP_SECKEY=HZqU7Y8EcTVzBi8ue8fHf9s6Dq-yxk1XxycfFwJv4bzzcjcTlYQi9iuYooDJK9AU480Mi6f0MvZBhIl0oc1f_Mugw0hvsBp18l5FuiWcL-IQpiM4eU1GqoM60jP8mQCuRx2hsT2L4d2g6AiRLErLyW_oa6fruHeMOFpJpKhbFWzVSGBDlSP0oizBZIHOr8YE; QN1=0000ef80306c58ba71a0951d; QN300=s%3Dbing; QN99=4763; QunarGlobal=10.66.42.199_-2c9240c1_18c020601c6_-779b|1700841524637; QN205=s%3Dbing; QN277=s%3Dbing; _i=VInJOADDZ-pq3O51YxVk1RWcdhqq; QN601=5195d7bef3bd9362263546af7a8ab1a5; QN48=0000f3002f1058ba71a81733; QN269=58C520A08AE211EE96D2FA163E763FD9; fid=b70d8d1a-ff47-4ec1-94ac-848c2f52ba9b; qunar-assist={%22version%22:%2220211215173359.925%22%2C%22show%22:false%2C%22audio%22:false%2C%22speed%22:%22middle%22%2C%22zomm%22:1%2C%22cursor%22:false%2C%22pointer%22:false%2C%22bigtext%22:false%2C%22overead%22:false%2C%22readscreen%22:false%2C%22theme%22:%22default%22}; csrfToken=TQ7h9NPXuUQmFKHGSWbStgLwsoEsvHsx; QN163=0; ariaDefaultTheme=null; QN57=17009724662160.6570329759305302; Hm_lvt_15577700f8ecddb1a927813c81166ade=1700972467; QN63=%E6%B7%B1%E5%9C%B3; _vi=5j_1Zki74VOZD9GydnBEpIXKkWrBfGbI0oVax6UGyvlbYQ4LTB7P7LSBrxaZgif10J1LSHsGKHbcgo_AZIDKiy3ys6EYYATbgUvzIBAfQdgnKk9COIpRIrSOawBc2XOnBYkgbq49AoFVncBLFXJEtr5s22npMkRAiX2ApDneRBIT; QN67=300%2C3341%2C2974%2C456656%2C1556%2C14753%2C13604%2C32468%2C14709%2C33631; QN58=1701089551647%7C1701089789417%7C2; Hm_lpvt_15577700f8ecddb1a927813c81166ade=1701089790; QN271=ef5fdc3c-cb05-45c1-8f6f-d1d9ef25949d; QN267=0737134915643076e6; JSESSIONID=B209C77346F33E8E0DE7459D195FC107; __qt=v1%7CVTJGc2RHVmtYMTh3MXlSS1RjczFXcVZTcWp2WEIvTUM4dmY5K2hDQVJkRWRHUndzeGoyTkg2UEl2WHBQalI0SXZESHB4Yi9VeTRFMmt4YlJCQU1JUWZ1blFRaGZpZG5RU1VBTFRjWndkMUQxSEFYckhLQXBGaVZuNW1xWHd5bk9sbHAyajdFMVNGS2Y0Z3Z2UWhaT3ZGeHVQUFZzZDNUM0VZTUtXU0NmbVVJPQ%3D%3D%7C1701094863974%7CVTJGc2RHVmtYMStQUUg5K3FvbHd1cGVQWUF2bFZJM1pYRW91SUFxODFGUlBJSGlBNlRUaDRESEFxejFvWEh0T3JINVJWRGNiTGZMUkxVcGczdCtDdnc9PQ%3D%3D%7CVTJGc2RHVmtYMTlhaUVad3FjZURieURoVjBOVHo4WTg1bkp3ejlad2VKSVlGSTJJcTNrQkZBMzI0MmVjNlBRZkNLdE9Tb1BFckE0ZnhzNVVQUEJzcXVCangzU1FIZ2RwSTMrOTcxdHJZbEVnTEpWcnU0ZURIb2ZQdlVSU1RJd2hMK3dKT1V6cjFCQkgyQTB6bmZseGxKYUtUamdQa1c5blBtVmxubG1hdUlvU280aVl0VStDdFROUGN4N25RejVURkdCTGdZOXUvR2Z6dmw1R29hUWd0YUQyeG1wdWV1clllMC9oUldLWWdETUZVTm5oU2dVR2pTQVVpTUtJRjFNaEVsZDZXY0NqbVNXeFpJQVpjZE5ZTGo0Mk9jS1ZRejdPZlUyalcxbzJ5enZuV3BLSUFlWWE4MmtPb0tMRzQ0dlFrdG9uTGYrVHoxL1oyZ3hKbEpCWTRqZHhUMnFZUmtGc1hFMEJTZktMM2ZyRUtyeWo3bHhkV1Rld0lUWHg1VSt3VlNGSllXWVlXenVBNUoveXBWYTNFWFRiczRadi84Q3hmaUNQRUs0RThyOFdpeUx3alBpZitMdGFFWGtRQ1lmUkdXWHNHdFdXQUh2RkFWZ2g2SXBEWXoyRjFhMWtiN3RXclliQ2tKSE45OEtFM2p2OTI3NnVXL29qUGNtUVFDRTZjNnFXdExDVGxHa0kySndiTDBCUGt3NlNZRm84ZkZ4Y0pnYk5MdE4rR2VtRVk1SzhuNnk4bGdaY2lmQmoxUHhqTG5IQ1h2Tm9XTjlRMCsxVlFLMytqeUZjL1l2K3F2TEJxaWJJVDJwdVhWYU9lNUluaFczbWFlTTNSejdGZk5XTGpOc3hlVFZVZWw4ZTh4ZXhxZ2pkTjJLM3hSVjFjU1ZLVTVFZG94RWF2cWh3NGFadmQ4Y0NzU2prT2pDSWlwM01VamNnMEd2dE9XR0ZXZTExdnNDU0Iva0Y5dHFkTk5CNk94eEEzaDBGaFE1WFRSWFBqeld5MjFMY0ZFNi80STBh'}
                # 对存在图片的发起保存操作，否则略过
                try:
                    res = request_get(photos_network, headers1)  # 导入用户代理、Cookie模拟登录函数
                    fw = open(save_path + str(a) + name.replace("·", "").replace('"', '') + '.jpg', 'wb')  # 当名字中带有特殊符号会导致报错
                    fw.write(res.content)
                    fw.close()
                    res.close()
                    a += 1
                except:
                    pass
        else:
            pass
        paragraph=get_infodetails(names,contents,bought_numbers,networks,moneies,paragraph)


def get_infodetails(names,contents,bought_numbers,networks,moneies,paragraph):
    advanceDayDescs_list=[]
    arrives_list=[]
    toTraffics_list=[]
    backTraffics_list=[]
    enids_list=[]
    travename_list=[]
    shopname_list=[]
    hotelstandard_list=[]
    visitspots_list=[]
    flag2 = '/fhx/detail'
    flag3='vendor'
    for network1 in networks:  # 将在景点提取出
        num1s = re.findall(#提取id值
            'https://touch.dujia.qunar.com/p/item/(.*?)\?date=.*?&amp;tuId=.*?&amp;order_source=tts_tuan',
            network1)  # \作为转义字符
        num2s = re.findall(#提取date值
            'https://touch.dujia.qunar.com/p/item/.*?\?date=(.*?)&amp;tuId=.*?&amp;order_source=tts_tuan', network1)
        num3s = re.findall(#提取tuid值
            'https://touch.dujia.qunar.com/p/item/.*?\?date=.*?&amp;tuId=(.*?)&amp;order_source=tts_tuan', network1)
        try:#此处针对含有（touch关键字的网址）
            network2 = 'https://touch.dujia.qunar.com/item?date={}&order_source=tts_tuan&tuId={}&id={}'.format(num3s[0],
                                                                                                               num2s[0],
                                                                                                               num1s[0])
            headers2 = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
                'Cookie': 'QN1=0000ef80306c58ba71a0951d; QN300=s%3Dbing; QN99=4763; QunarGlobal=10.66.42.199_-2c9240c1_18c020601c6_-779b|1700841524637; _i=VInJOADDZ-pq3O51YxVk1RWcdhqq; QN601=5195d7bef3bd9362263546af7a8ab1a5; QN48=0000f3002f1058ba71a81733; QN269=58C520A08AE211EE96D2FA163E763FD9; fid=b70d8d1a-ff47-4ec1-94ac-848c2f52ba9b; ariaDefaultTheme=null; QN57=17009724662160.6570329759305302; qunar-assist={%22version%22:%2220211215173359.925%22%2C%22show%22:false%2C%22audio%22:false%2C%22speed%22:%22middle%22%2C%22zomm%22:1%2C%22cursor%22:false%2C%22pointer%22:false%2C%22bigtext%22:false%2C%22overead%22:false%2C%22readscreen%22:false%2C%22theme%22:%22default%22}; csrfToken=rBAInlCJurP8mW8Zbk71I4djIRct3G27; QN163=0; QN205=s%3Dbing; activityClose=1; HN1=v1192cf7380ad0bfe28d0b56c2a3e91e8b; HN2=qkzzcqgsrngkk; ctt_june=1683616182042##iK3wWK3wWhPwawPwa%3DjmVDjmXPfDaRXnXSHIXKWDX%3DDsXSa8WRiTX%3DXwERvmiK3siK3saKg8aKg8WKt%3DWKjOVuPwaUvt; QN621=1490067914133%252Ctestssong%3DDEFAULT%26fr%3Dtejia_inter_search; quinn=c51b76ae9ed8ed8962e547a570ca5128bd3596eec5a1ed7fff304849f83a38ea2389c2594cef6b413d6380bd57770186; QN277=s%3Dbing; QN25=5423d6aa-e0f3-42c0-b766-4052541e1abb-9f992f90; ctf_june=1683616182042##iK3waKjNWhPwawPwasj8aD3AaS3AX2XnXSX%2BVRD%2BWs3OE2jsa2XnVPDAas3%2BiK3siK3saKg8aKg%3DVRP8aKa%2BauPwaUvt; cs_june=0bc7f90a047416308e4053925af0f25b57de51ee818fa7390f53182397a6a6ff1903b574ba839acc60b81c2803d03ae779bf3ba73f7c5b86d6746dedc568af80b17c80df7eee7c02a9c1a6a5b97c1179f1c4e159c7b7a221233bf32c89647a925a737ae180251ef5be23400b098dd8ca; QN58=1701748521264%7C1701748991946%7C5; _vi=QA2be5u4hohhGpUUfPNn4RvkIVBmWcW_HTT8cxzHY8bQSSpY0OR-x3-7XX3sLGrJOx6faZi2i9bpSf5XJVBBFPRraSG2bWz_lZ5WAkHQvrepts2_hlqEXlpy4FTiN0eZ8gJq8Zh94wgSf3Y9b8UQiRAulDY8geYv01WUH_gkLsm4; QN271=d896572a-74de-4c28-8708-e006ebbcbac2; QN243=165; QN267=0737134915edf6bee2'}
            res = request_get(network2, headers2)
            time.sleep(1)
            html = res.text
            advanceDayDescs,arrives,toTraffics,backTraffics,enids,travename,shopname,hotelstandard,visitspots=json_infos(html)
            advanceDayDescs_list.append(advanceDayDescs)
            arrives_list.append(arrives)
            toTraffics_list.append(toTraffics)
            backTraffics_list.append(backTraffics)
            enids_list.append(enids)
            travename_list.append(travename)
            shopname_list.append(shopname)
            hotelstandard_list.append(hotelstandard)
            visitspots_list.append(visitspots)
        except:
            if flag3 in network1:
                try:
                    headers2 = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
                        'Cookie': 'QN1=0000ef80306c58ba71a0951d; QN300=s%3Dbing; QN99=4763; QunarGlobal=10.66.42.199_-2c9240c1_18c020601c6_-779b|1700841524637; _i=VInJOADDZ-pq3O51YxVk1RWcdhqq; QN601=5195d7bef3bd9362263546af7a8ab1a5; QN48=0000f3002f1058ba71a81733; QN269=58C520A08AE211EE96D2FA163E763FD9; fid=b70d8d1a-ff47-4ec1-94ac-848c2f52ba9b; ariaDefaultTheme=null; QN57=17009724662160.6570329759305302; qunar-assist={%22version%22:%2220211215173359.925%22%2C%22show%22:false%2C%22audio%22:false%2C%22speed%22:%22middle%22%2C%22zomm%22:1%2C%22cursor%22:false%2C%22pointer%22:false%2C%22bigtext%22:false%2C%22overead%22:false%2C%22readscreen%22:false%2C%22theme%22:%22default%22}; csrfToken=rBAInlCJurP8mW8Zbk71I4djIRct3G27; QN163=0; QN205=s%3Dbing; activityClose=1; HN1=v1192cf7380ad0bfe28d0b56c2a3e91e8b; HN2=qkzzcqgsrngkk; ctt_june=1683616182042##iK3wWK3wWhPwawPwa%3DjmVDjmXPfDaRXnXSHIXKWDX%3DDsXSa8WRiTX%3DXwERvmiK3siK3saKg8aKg8WKt%3DWKjOVuPwaUvt; QN621=1490067914133%252Ctestssong%3DDEFAULT%26fr%3Dtejia_inter_search; quinn=c51b76ae9ed8ed8962e547a570ca5128bd3596eec5a1ed7fff304849f83a38ea2389c2594cef6b413d6380bd57770186; QN277=s%3Dbing; QN25=5423d6aa-e0f3-42c0-b766-4052541e1abb-9f992f90; ctf_june=1683616182042##iK3waKjNWhPwawPwasj8aD3AaS3AX2XnXSX%2BVRD%2BWs3OE2jsa2XnVPDAas3%2BiK3siK3saKg8aKg%3DVRP8aKa%2BauPwaUvt; cs_june=0bc7f90a047416308e4053925af0f25b57de51ee818fa7390f53182397a6a6ff1903b574ba839acc60b81c2803d03ae779bf3ba73f7c5b86d6746dedc568af80b17c80df7eee7c02a9c1a6a5b97c1179f1c4e159c7b7a221233bf32c89647a925a737ae180251ef5be23400b098dd8ca; QN58=1701748521264%7C1701748991946%7C5; _vi=QA2be5u4hohhGpUUfPNn4RvkIVBmWcW_HTT8cxzHY8bQSSpY0OR-x3-7XX3sLGrJOx6faZi2i9bpSf5XJVBBFPRraSG2bWz_lZ5WAkHQvrepts2_hlqEXlpy4FTiN0eZ8gJq8Zh94wgSf3Y9b8UQiRAulDY8geYv01WUH_gkLsm4; QN271=d896572a-74de-4c28-8708-e006ebbcbac2; QN243=165; QN267=0737134915edf6bee2'}
                    network = network1.replace('//','https://')
                    detailinfos3_href=get_detailinfos3_href(network,headers2)
                    advanceDayDescs, arrives, toTraffics, backTraffics, enids, travename, shopname, hotelstandard, visitspots = get_detailinfos3(
                        detailinfos3_href,headers2)
                    advanceDayDescs_list.append(advanceDayDescs)
                    arrives_list.append(arrives)
                    toTraffics_list.append(toTraffics)
                    backTraffics_list.append(backTraffics)
                    enids_list.append(enids)
                    travename_list.append(travename)
                    shopname_list.append(shopname)
                    hotelstandard_list.append(hotelstandard)
                    visitspots_list.append(visitspots)
                except:
                    network = network1.replace('//', 'https://')
                    advanceDayDescs, arrives, toTraffics, backTraffics, enids, travename, shopname, hotelstandard, visitspots = get_detailinfos2(
                        network)
                    advanceDayDescs_list.append(advanceDayDescs)
                    arrives_list.append(arrives)
                    toTraffics_list.append(toTraffics)
                    backTraffics_list.append(backTraffics)
                    enids_list.append(enids)
                    travename_list.append(travename)
                    shopname_list.append(shopname)
                    hotelstandard_list.append(hotelstandard)
                    visitspots_list.append(visitspots)



    save_infos(names,contents,bought_numbers,moneies,enids_list,networks,advanceDayDescs_list,arrives_list,toTraffics_list,
               backTraffics_list,travename_list,shopname_list,hotelstandard_list,visitspots_list)
    paragraph = paragraph + 1
    return paragraph

if __name__=='__main__':
    # 建立相关文档（csv、txt）、后台所要存储的数据库
    fp = open("./Qunar_Infos.csv", "a",newline='', encoding='utf-8-sig')
    writer = csv.writer(fp)
    writer.writerow(["团购名称",
                 "旅行内容",
                 "已购人数",
                 "旅游ID",
                 "价格/1人",
                 "团购网址",
                 "注意事项",
                 "目的地景点",
                 "去的方式",
                 "回来的方式",
                 "团购公司",
                 "团购发布来源",
                 "住宿条件",
                 "浏览的总个数"])

    client = pymongo.MongoClient('localhost', 27017)
    mydb = client['mydb']
    Qunar_Infos = mydb['Qunar_Infos']

    conn = pymysql.connect(host='localhost' , user='root' , password='Clj3208147' , db='mydb', port=3306 , charset='utf8mb4')
    cursor = conn.cursor()

    fw = open("./Qunar.txt", "a", encoding="utf-8")

    # 这里利用Selenium进行浏览器行为的模拟
    driver = webdriver.Chrome()
    # 最大化浏览器窗口
    driver.maximize_window()
    # 通过driver.get方法对目标浏览器发起请求，返回对方的源代码
    driver.get('https://www.qunar.com/')
    # 登录到去哪儿网主页面，设置显式等待时间，等待网页刷新，通过css_selector定位团购按钮
    wait = WebDriverWait(driver, 10)
    bought=driver.find_element(by=By.CSS_SELECTOR,
                               value='body > div.q_header.q_header_home.home_header_201909_4004 > div.d'
                              'iv_mnav.qunar-assist-hide > div.q_header_mnav.qunar-assist-hide > ul >'
                              ' li:nth-child(6) > a > span > b')
    # 模拟点击团购按钮
    bought.click()
    # 通过css_selector定位"长线游"按钮
    long_trip=driver.find_element(by=By.CSS_SELECTOR,value='#tuan-nav > div > div > ul > li:nth-child(3) > a')
    # 模拟点击“长线游”按钮
    long_trip.click()
    # 登录到团购列表主页面，设置等待时间，等待网页刷新
    driver.implicitly_wait(10)
    # 模拟下拉滑动条
    driver_execute_script()
    dom=etree.HTML(driver.page_source)
    page=eval(input("请输入要查询的页数:"))
    paragraph = 1
    get_infos(page,paragraph)
    fw.close()
    jieba.setLogLevel(jieba.logging.INFO)
    jieba_creation()
