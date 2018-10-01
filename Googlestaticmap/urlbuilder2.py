"!/usr/bin/python"
import requests
from pylatex import Document, Section, Subsection, Tabular, Math, TikZ, Axis, \
    Plot, Figure, Matrix, Alignat
from pylatex.utils import italic
import os
import psycopg2

#assuming the input data will be an array
def get_parts():
    """  connection to Kharto DB & query for markers  """
    conn = None
    try:
        conn = psycopg2.connect(database='Kharto', user='Kharto', port='5432', host = 'localhost')
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT dc.facility_id,TRIM ( trailing ')'from (TRIM (leading 'POINT (' from ST_AsText(ST_CENTROID(ST_UNION(existing_coordinates::geometry)))))) AS center,TRIM (trailing ')'from (TRIM (leading 'MULTIPOINT (' from ST_AsText(ST_UNION(existing_coordinates::geometry)))))AS locations from lms.lms_towers_raw tow,lms.lms_applications_raw app,daisy_chain.facility_chains dc WHERE app.app_key = tow.app_key AND app.facility_id = ANY(dc.dependencies||dc.dependents||dc.lss_groupmates) AND app.app_key IN (SELECT app_key FROM lms_399_list) GROUP BY dc.facility_id ORDER BY facility_id DESC;")
        rows = cur.fetchone()
        mylist = []
        mylist = rows[2].split(",")
        print (mylist)
        cur.close()
        return mylist
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

#variables that hold the path color ,this will change based on the condtions for color
path_color1 = "red"
path_color2 = "blue"
marker_color = "green"
#function to build the Url of the marker locations in mylist variable
def makeurl(ourlist):
    #url path built based on Google Static Map API documentation
    url = "http://maps.google.com/maps/api/staticmap?size=400x400&scale=2&maptype=terrain"
    path_start = f"&path=color:{path_color1}%7Cweight:3|"
    path_end = "|"
    path_middle = ""
    for i in ourlist:
        value_index = ourlist.index(i)
        index_len = len(ourlist)-1
        mlng,mlat = i.split(" ")
        if value_index == 0:
            path_start += f"{mlat},{mlng}"
        elif value_index == index_len:
            path_end += f"{mlat},{mlng}"
        else:
            path_middle += f"|{mlat},{mlng}&path=color:{path_color2}%7Cweight:3|{mlat},{mlng}"
        url += f"&markers=size:tiny%7Ccolor:{marker_color}%7Clabel:1%7C{mlat},{mlng}"
    return url + path_start + path_middle + path_end

if __name__ == '__main__':

    marker_list = get_parts()
    myurl = makeurl(marker_list)
    #the Google static map URL to be passed as a http request and get a map image in PNG format
    r = requests.get(myurl, allow_redirects=True)
    open('image.png', 'wb').write(r.content)
    image_filename = os.path.join(os.path.dirname(__file__), 'image.png')
    geometry_options = {"tmargin": "5cm", "lmargin": "5cm"}
    doc = Document(geometry_options=geometry_options)

    #create a latex document
    with doc.create(Subsection('pictures')):
        with doc.create(Figure(position='h!')) as map_pic:
            map_pic.add_image(image_filename, width='200px')
            map_pic.add_caption('Look it\'s its a map')

    #generate the final PDF
    doc.generate_pdf('C:/Users/Tanya Sharma/Desktop/finalmap', clean_tex=False)
