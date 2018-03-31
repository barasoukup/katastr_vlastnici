# -*- coding: utf-8 -*-
"""
Created on 2018-03-05

@author: matej
"""

import requests
from bs4 import BeautifulSoup
import json
import csv

src = 'sample_input.geojson'
out = 'out.geojson'
vlastnici_csv ='vlastnici.csv'
vlastnici_json = 'vlastnici.json'



def update_info(pozemek):
    prava = []
    x = round(pozemek["geometry"]["coordinates"][0])
    y = round(pozemek["geometry"]["coordinates"][1])
    spravna = False
    for korekce in [(0,0),(-1,0),(1,0),(0,1),(0,-1),(-1,-1),(-1,1),(1,-1),(1,1)]:
        url = "http://nahlizenidokn.cuzk.cz/MapaIdentifikace.aspx?l=KN&x="+str(x+korekce[0])+"&y="+str(y+korekce[1])
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
    #info o parcele
        atributy = soup.find(summary="Atributy parcely")
        if atributy:
            print(atributy.find_next("td").find_next("td").text)
            if atributy.find_next("td").find_next("td").text == pozemek["properties"]["TEXT_KM"]:
                spravna = True
                break
        else:
            print(soup)
            break
    print(spravna)
    if not spravna:
        print("Nepodarilo se zjistit informace o parcele",pozemek["properties"]["TEXT_KM"])
    else:
        for row in atributy.find_all("tr"):
            pozemek["properties"][row.find_next("td").text]=row.find_next("td").find_next("td").text
            #print(row.find_next().text, row.find_next().find_next().text)
    #vlastnici
        vlastnici = soup.find(summary="Vlastníci, jiní oprávnění")
        row = vlastnici.find_next("tr")
        while row:
            nt = row.find_next()
            nt2 = nt.find_next()
            if nt.name == "th":
                pravo = nt.text
            elif nt.name == "td":
                subjekt = nt.text[:-2]
                podil_t = nt2.text
                if podil_t == "":
                    podil_t = "1"
                    podil = 1
                else:
                    citatel,jmenovatel = podil_t.split("/")
                    podil = float(citatel)/float(jmenovatel)     
                print("\t"+pravo, subjekt,podil_t, podil, sep='; ')
                prava.append([pravo, subjekt, podil_t, podil])
            row = row.find_next("tr")
        return prava

def vlastnik_hospodar_label(prava):
    vlastnici = []
    hospodari = []
    vlastnik_label = ""
    hospodar_label = ""
    for pravo in prava:
        if pravo[0] in (u"Vlastnické právo", u"Duplicitní zápis vlastnictví"):
            vlastnici.append(pravo)
        elif pravo[0] in (u"Právo hospodařit s majetkem státu",u"Právo hospodaření s majetkem státu",u"Hospodaření se svěřeným majetkem kraje",u"Příslušnost hospodařit s majetkem státu"):
            hospodari.append(pravo)
    dalsi=0
    names=[]
    if len(vlastnici)==1:
        vlastnik_label = vlastnici[0][1]
    else:
        for vlastnik in sorted(vlastnici, key=lambda x: x[3], reverse=True):
            if vlastnik[3] >=0.2:
                names.append(vlastnik[1]+" ("+str("%.2f" % vlastnik[3]).rstrip("0")+")")
            else:
                dalsi+=1
        if names:
            vlastnik_label = ", ".join(names)
            if dalsi>0:
                vlastnik_label+= u" a dalších "+str(dalsi)
        else:
            vlastnik_label = str(dalsi)+u" vlastníků"

    dalsi=0
    names=[]
    if len(hospodari)==1:
        hospodar_label = hospodari[0][1]
    elif len(hospodari)>1:
        for hospodar in sorted(hospodari, key=lambda x: x[3], reverse=True):
            if hospodar[3] >=0.2:
                names.append(hospodar[1]+" ("+str("%.2f" % hospodar[3]).rstrip("0")+")")
            else:
                dalsi+=1
        if names:
            hospodar_label = ", ".join(names)
            if dalsi>0:
                hospodar_label+= u" a dalších "+str(dalsi)
        else:
            hospodar_label = str(dalsi)+u" hospodářů"

    return  vlastnik_label,hospodar_label

    

if __name__ == "__main__":

    vlastnici_dict = {}
    
    with open(src) as data_file:    
        data = json.load(data_file)
    features = data["features"]
    for pozemek in features:
        print(pozemek["properties"]["TEXT_KM"])
        if not "Vlastník" in pozemek["properties"]:
            prava = update_info(pozemek)
            vlastnici_dict[pozemek["properties"]["ID_2"]] = prava
            vlastnik_label,hospodar_label = vlastnik_hospodar_label(prava)
            pozemek["properties"]["Vlastník"]=vlastnik_label
            pozemek["properties"]["Hospodář"]=hospodar_label

    with open(out, 'w') as outfile:
        json.dump(data, outfile)

    with open(vlastnici_json, 'w') as outfile:
        json.dump(vlastnici_dict, outfile)

    with open(vlastnici_csv,'w') as out:
        csv_out=csv.writer(out)
        csv_out.writerow(['ID_2','Pravo','Subjekt','Podil_text', 'Podil_int'])
        for key in vlastnici_dict:
            zaznamy = vlastnici_dict[key]
            for val in zaznamy:
                row = [key, val[0], val[1], val[2], val[3]]
                csv_out.writerow(row)

            
    
    
