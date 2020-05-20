import pandas
import geopandas
import shapely
from shapely.geometry import Polygon
from shapely.geometry import shape
from datetime import datetime,timedelta
import os
import sys
from OSMPythonTools.api import Api
from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder,Overpass

class datoteka:
    def __init__(self,putanja):
        self.putanja=putanja
    def odabir_datoteke(self):
        print("ODABERITE .CSV DATOTEKU")
        files=[]
        selection=[]
        i=0
        for file_name in os.listdir(os.getcwd()):
            if file_name.endswith('.csv') or file_name.endswith('.CSV'):
                print(str(i)+" --> "+str(file_name))
                files.append(file_name)
                i=i+1
        if i==0:
            print("NEMA .CSV DATOTEKA")
            sys.exit()
        print(str(i)+" --> "+"SVE .CSV DATOTEKE")
        print("(U slučaju višestrukog izbora odabir odvojite zarezom --> 0,1,2,3...)")
        file_number=input("---> ")
        if file_number==str(i):
            print("ODABRALI STE SVE .CSV DATOETEKE")
            selection=files
        else:
            file_nmbs=file_number.split(",")
            int_file_nmbs=[]
            for j in range(0,len(file_nmbs)):
                int_file_nmb=int(file_nmbs[j])
                if int_file_nmb not in range(0,i+1):
                    print(str(int_file_nmb)+"--> POGREŠAN BROJ DATOTEKE")
                else:
                    int_file_nmbs.append(int_file_nmb)
            print("Odabrano je: ")
            for ime in range(0,len(int_file_nmbs)):
                print(files[int_file_nmbs[ime]])
                selection.append(files[int_file_nmbs[ime]])
        return selection

class metadata:
    TIME_FORMAT="%H:%M:%S.%f"
    def __init__(self,NAME,MISSION,TIMESTAMP,FRAMESTAMP,GEOMETRY):
        self.NAME=NAME
        self.MISSION=MISSION
        self.TIMESTAMP=TIMESTAMP
        self.FRAMESTAMP=FRAMESTAMP
        self.GEOMETRY=GEOMETRY
    def frametime(self,dataframe,TIME_COL):
        start=dataframe.loc[0,TIME_COL]
        start_time=start[11:(len(start)-1)]
        end=dataframe.loc[((len(dataframe))-1),TIME_COL]
        end_time=end[11:(len(start)-1)]
        time_delta=datetime.strptime(end_time,metadata.TIME_FORMAT)-datetime.strptime(start_time,metadata.TIME_FORMAT)
        frame_time=time_delta/len(dataframe)
        print("Trajanje snimke: "+str(time_delta))
        print("Trajanje frame-a: "+str(frame_time))
        print("Broj frame-ova: "+str(len(df)))
        return frame_time

    def arhiviranje(self,gpkg_path,frames_gdf,lista_datoteka,datoteka_iz_liste):
        gpkg_check=os.path.exists(gpkg_path)
        if gpkg_check is True:
            print("USPJEŠNO PRONAĐENA POSTOJEĆA GPKG ARHIVA")
            Frames=geopandas.read_file("MISB_MetadataDB.gpkg",layer="Frames",driver="GPKG")
            print(Frames)
            update_Frames=geopandas.GeoDataFrame(pandas.concat([Frames,frames_gdf],ignore_index=True),crs="EPSG:4326")
            update_Frames.to_file("MISB_MetadataDB.gpkg",layer="Frames",driver="GPKG")
            print(update_Frames)
            print("ARHIVA JE AŽURIRANA")
            print("STATUS: "+str(lista_datoteka.index(datoteka_iz_liste)+1)+"/"+str(len(lista_datoteka)))
        else:
            print(frames_gdf)
            frames_gdf.to_file("MISB_MetadataDB.gpkg",layer="Frames",driver="GPKG")
            print("STVORENA JE NOVA GPKG ARHIVA")
            print("STATUS: "+str(lista_datoteka.index(datoteka_iz_liste)+1)+"/"+str(len(lista_datoteka)))


class osm_military:
    def __init__(self,NAME):
        self.NAME=NAME
    def query_construction(self,search_area):
        nominatim_query=Nominatim().query(search_area)
        query_01=overpassQueryBuilder(area=nominatim_query.areaId(),elementType=['node','way','relation'], selector=["military"],includeGeometry=True)
        query_02=overpassQueryBuilder(area=nominatim_query.areaId(),elementType=['node','way','relation'], selector='"landuse"="military"',includeGeometry=True)
        result_01=Overpass().query(query_01)
        result_02=Overpass().query(query_02)
        print("Pronađeno ukupno "+str(result_01.countElements())+" 'military' objekta")
        print("Pronađeno ukupno "+str(result_02.countElements())+" 'landuse=military' objekta")
        results=[result_01,result_02]
        return results

    def atributi(self,query_result,atribut):
        opis=[]
        for i in range(0,query_result.countElements()):
            tagovi=query_result.elements()[i].tags()
            if atribut in tagovi:
                description=tagovi.get(atribut)
                opis.append(description)
            else: opis.append(None)
        return opis

    def query_geometrija(self,query_result):
        geometry=[]
        for i in range(0,query_result.countElements()):
            geometrija=shape(query_result.elements()[i].geometry())
            geometry.append(geometrija.wkt)
        return geometry

class analiza:
    def snimke_s_objektima(self,analysis_dataframe):
        snimke=analysis_dataframe["Naziv snimke"].unique()
        print("Snimke na kojima su vidljivi vojni objekti:")
        for s in snimke:
            print(" --> "+s)
        print("Ukupno: "+str(len(snimke)))
        return snimke

    def objekti_na_snimkama(self,analysis_dataframe):
        mil_obj=analysis_dataframe["name"].unique()
        print("Vojni objekti koji su vidljivi na snimkama:")
        for o in mil_obj:
            print(" --> "+o)
        print("Ukupno: "+str(len(mil_obj)))
        return mil_obj

    def lista_objekata_za_snimak(self,dataframe,snimak):
        mil_obj=dataframe["name"].unique()
        n_obj=[]
        for obj in mil_obj:
            for i in range(0,len(dataframe)):
                if dataframe.loc[i,"Naziv snimke"]==snimak and dataframe.loc[i,"name"]==obj:
                        n_obj.append(obj)
        objekti=[]
        for j in set(n_obj):
            objekti.append(j)
        return objekti

    def lista_vremena(self,dataframe,snimak,objekt):
        t_obj=[]
        for i in range(0,len(dataframe)):
            if dataframe.loc[i,"Naziv snimke"]==snimak and dataframe.loc[i,"name"]==objekt:
                    t_obj.append(df.loc[i,"Vrijeme frame-a"])
        return t_obj

    def segmentiranje(self,time_list):
        TIME_FORMAT="%H:%M:%S.%f"
        step=timedelta(seconds=1)
        unsorted_timelist=[]
        timetable=[]
        for t in range(0,len(time_list)):
            unsorted_timelist.append(datetime.strptime(time_list[t],TIME_FORMAT))
        timelist=sorted(unsorted_timelist)
        for time in range(1,len(timelist)):
            current_frame=timelist[(time-1)]
            next_frame=timelist[time]
            delta=next_frame-current_frame
            if delta>step:
                segment_endtime=current_frame
                segment_starttime=next_frame
                timetable.append(segment_endtime)
                timetable.append(segment_starttime)
            else: continue
        if len(timetable)!=0:
            timetable.insert(0,timelist[0])
            timetable.insert(len(timetable),timelist[(len(timelist))-1])
            for dt in range(0,len(timetable)):
                timetable[dt]=datetime.strftime(timetable[dt],TIME_FORMAT)
        elif len(timetable)==0:
            timetable.append(timelist[0])
            timetable.append(timelist[-1])
            for dt in range(0,len(timetable)):
                timetable[dt]=datetime.strftime(timetable[dt],TIME_FORMAT)
        parovi=[]
        if len(timetable)%2 == 0:
            for i in range(0,len(timetable),2):
                parovi.append("("+timetable[i]+" - "+timetable[i+1]+")")
        return parovi

#############################
#### UČITAVANJE PODATAKA ####
#############################
print(os.getcwd())
print("POTVRDITE DA JE OVO VAŠ RADNI DIREKTORIJ: "+os.getcwd())
print("0 - NE \n1 - DA")
unos=int(input("--> "))
if unos==0:
    print("UNESITE ISPRAVNU PUTANJU VAŠEG RADNOG DIREKTORIJA: \n>>> Napomena: Putanja ne smije završavati s znakom '\\' <<<)")
    novi_cwd=input("--> ")
    os.chdir(novi_cwd)
    print("NOVI RADNI DIREKTORIJ JE: "+os.getcwd())
    ime_datoteke=datoteka.odabir_datoteke(datoteka)
elif unos==1:
    ime_datoteke=datoteka.odabir_datoteke(datoteka)
else: print("NISTE UNIJELI ODGOVARAJUĆI BROJ")


for files in ime_datoteke:
    if os.getcwd().startswith('/'):
        datoteka.putanja=os.getcwd()+"/"+files
    else:
        datoteka.putanja=os.getcwd()+"\\"+files
    df=pandas.read_csv(datoteka.putanja)
    MISSION_COL="Mission ID"
    if set(["UNIX Time Stamp"]).issubset(df.columns):
        TIME_COL="UNIX Time Stamp"
        LONG_COLS=["Corner Longitude Point 4","Corner Longitude Point 3","Corner Longitude Point 2","Corner Longitude Point 1"]
        LAT_COLS=["Corner Latitude Point 4","Corner Latitude Point 3","Corner Latitude Point 2","Corner Latitude Point 1"]
    elif set(["Precision Time Stamp"]).issubset(df.columns):
        TIME_COL="Precision Time Stamp"
        for time in range(0,len(df)):
            timestamp_df=str(df.loc[time,TIME_COL])
            timestamp_slice=timestamp_df[0:10]+"."+timestamp_df[11:]
            timestamp_float=float(timestamp_slice)
            metadata.TIMESTAMP=datetime.fromtimestamp(timestamp_float)
            df.loc[time,TIME_COL]=datetime.strftime(metadata.TIMESTAMP,"%Y-%m-%d %H:%M:%S.%f")+"Z"
        LONG_COLS=["Offset Corner Longitude Point 4","Offset Corner Longitude Point 3","Offset Corner Longitude Point 2","Offset Corner Longitude Point 1"]
        LAT_COLS=["Offset Corner Latitude Point 4","Offset Corner Latitude Point 3","Offset Corner Latitude Point 2","Offset Corner Latitude Point 1"]
    else:
        print("NE POSTOJI ODGOVARAJUĆA KOLONA VREMENA")


    print("Snimka: "+files)
    frame_time=metadata.frametime(metadata,df,TIME_COL)

    frames_gdf=geopandas.GeoDataFrame(data=None,columns=['Naziv snimke','Naziv misije','Datum i vrijeme','Vrijeme frame-a','geometry'],crs="EPSG:4326")
    vrijeme_frame=[]
    naziv_snimke=[]
    invalid_geom=[]

    for frame in range(0,len(df)):
        poligon=[]
        for i in range(0,4):
            x=df.loc[frame,LONG_COLS[i]]
            y=df.loc[frame,LAT_COLS[i]]
            koordinate=(x,y)
            poligon.append(koordinate)
        naziv_snimke.append(files.replace(".csv","").replace(".CSV","").replace("VideoMetadataToFeatureClass_CsvFile__",""))
        frames_gdf.loc[frame,'Naziv snimke']=naziv_snimke[frame]
        metadata.NAME=naziv_snimke[frame]
        frames_gdf.loc[frame,'Naziv misije']=df.loc[frame,MISSION_COL]
        metadata.MISSION=df.loc[frame,MISSION_COL]
        frames_gdf.loc[frame,'Datum i vrijeme']=df.loc[frame,TIME_COL]
        vrijeme_frame.append(str(frame_time*(frame+1)))
        frames_gdf.loc[frame,'Vrijeme frame-a']=vrijeme_frame[frame]
        metadata.FRAMESTAMP=vrijeme_frame[frame]
        try:
            geometrija=Polygon(poligon)
            frames_gdf.loc[frame,'geometry']=geometrija
            metadata.GEOMETRY=geometrija
        except ValueError:
            frames_gdf.loc[frame,'geometry']=None
            metadata.GEOMETRY=None
            invalid_geom.append(frame)
            print("Frame broj "+str(frame)+" nema ispravnu geometriju")

    frames_gdf=frames_gdf.drop(invalid_geom).reset_index(drop=True)
    print("Broj obrađenih frame-ova: "+str(len(frames_gdf)))
    print("Broj neupotrebljivih frame-ova "+str(len(df)-len(frames_gdf)))

    if os.getcwd().startswith('/'):
        gpkg_path=os.getcwd()+"/"+"MISB_MetadataDB.gpkg"
    else:
        gpkg_path=os.getcwd()+"\\"+"MISB_MetadataDB.gpkg"

    metadata.arhiviranje(metadata,gpkg_path,frames_gdf,ime_datoteke,files)

####################################
#### PRETRAŽIVANJE OSM PODATAKA ####
####################################
results=osm_military.query_construction(osm_military,"Croatia")

columns=["name","old_name","alt_name","military","description",'location']
gdf=geopandas.GeoDataFrame(data=None,columns=(columns+["geometry"]),crs="EPSG:4326")
print(gdf)

for res in results:
    lim=len(gdf)
    for cols in columns:
        lim_v=0+lim
        for i in osm_military.atributi(osm_military,res,cols):
            gdf.loc[lim_v,cols]=i
            lim_v=lim_v+1
    for geom in osm_military.query_geometrija(osm_military,res):
        gdf.loc[lim,'geometry']=shapely.wkt.loads(geom)
        lim=lim+1
gdf_clean=gdf.drop_duplicates().reset_index(drop=True)
print("Unutar pronađenih rezultata obrisano je "+str((len(gdf)-len(gdf_clean)))+" duplikata.")
print("Pronađeno je "+str((len(gdf)-(len(gdf)-len(gdf_clean))))+" različitih 'military'/'landuse:military' objekta")

for obj in range(0,len(gdf_clean)):
    if gdf_clean.loc[obj,'name']==None:
        gdf_clean.loc[obj,'name']="UNK_Obj_"+str(obj)
        osm_military.NAME=gdf_clean.loc[obj,'name']
    else:
        osm_military.NAME=gdf_clean.loc[obj,'name']


print(gdf_clean)
####################################
#### PROSTORNA ANALIZA PODATAKA ####
####################################
Frames=geopandas.read_file("MISB_MetadataDB.gpkg",layer="Frames",driver="GPKG")
print(Frames)
analysis_df=pandas.DataFrame(data=None,columns=(columns+["Vrijeme frame-a"]+["Naziv snimke"]+["Datum i vrijeme"]))
for military in range(0,len(gdf_clean)):
    for frames in range(0,len(Frames)):
        if gdf_clean.loc[military,'geometry'].intersects(Frames.loc[frames,'geometry']):
            analysis_df.loc[frames,columns]=gdf_clean.loc[military,:'geometry']
            analysis_df.loc[frames,'Vrijeme frame-a']=Frames.loc[frames,'Vrijeme frame-a']
            analysis_df.loc[frames,'Naziv snimke']=Frames.loc[frames,'Naziv snimke']
            analysis_df.loc[frames,'Datum i vrijeme']=Frames.loc[frames,'Datum i vrijeme']
        else:
            continue
print(analysis_df)
analysis_df.to_csv("SpatialAnalysis.csv")
print("REZULTATI ANALIZE SPREMLJENI U RADNOM DIREKTORIJU --> 'SpatialAnalysis.csv'")
####################################
#### RAŠČLAMBA ANALIZE PODATAKA ####
####################################
df=pandas.read_csv("SpatialAnalysis.csv")
print("-------------------------------------")
print("RAŠČLAMBA REZULTATA ANALIZE SNIMAKA")
print("-------------------------------------")
snimke=analiza.snimke_s_objektima(analiza,df)
print("************")
objekti=analiza.objekti_na_snimkama(analiza,df)
print("************")

for snimak in snimke:
    print("Snimka "+str(snimak)+" sadrži sljedeće vojne objekte u navedenom vremenu:")
    vojni_objekti=analiza.lista_objekata_za_snimak(analiza,df,snimak)
    for obj in vojni_objekti:
        print("--> "+obj)
        time_list=analiza.lista_vremena(analiza,df,snimak,obj)
        video_time=analiza.segmentiranje(analiza,time_list)
        for vt in video_time:
            print(vt)
    print("Ukupno: "+str(len(vojni_objekti)))
    print("************")
