__author__ = 'sgarlapa'

import sys

def createPerformanceFile(url_list):
    #Parsing
    filename_perf = "sampleinput/mobilePerformance.json"
    performance_file = open(filename_perf,'w')

    #Login flow is added since selenium config file doesn't have it
    performance_file.write(" { \"name\" : \"LinkedIn Mobile Login\", \"navigation\": [")
    performance_file.write(" [ { \"type\": \"navigate\", \"params\": { \"url\": \"https://touch.www.linkedin.com/login.html\"},\
       \"page-name\": \"Login Page\",\"network-timeout\": 1  } ],\
        [ { \"type\": \"textfield-set\",\"params\": {\"id\": \"username\",\"value\": \"user2008@correo.linkedinlabs.com\"}},\
        { \"type\": \"textfield-set\",\"params\": {\"id\": \"password\",\"value\": \"password\"} },\
        { \"type\": \"click\",\"params\": {\"id\": \"login-button\"},\"page-name\": \"Member Home Page\",\
        \"network-timeout\": 2} ],")

    for i in url_list:
        performance_file.write(",",)
        performance_file.write("[ { \"type\": \"navigate\",")
        performance_file.write("\"params\": {\"url\": \"https://touch.www.linkedin.com/")
        performance_file.write(i)
        performance_file.write("},\"page-name\": \"Mobile page -")
        performance_file.write(i)
        performance_file.write(",\"network-timeout\": 1  } ]")


def main():

    filename= sys.argv[1]
    qa_file= open(filename,'r')
    mobile_url = ""
    url_list = []

    for line in qa_file :
        if '/#' in line :
        # print "line:",line
            begin_index=line.find('#')
            # print begin_index

            if ':' in line :
                end_index = line.find(':')

                mobile_url = line[begin_index:end_index-1]
                url_list.append(mobile_url)
                # else :
                # print "not found"

                # print mobile_url

    print url_list
    createPerformanceFile(url_list)



if __name__=="__main__":
    main()
