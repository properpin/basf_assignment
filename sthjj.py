import scrapy
import os
import json
import zipfile
import io
import re


class uvpSpider(scrapy.Spider):
    name = "sthjj_spider"
    current_project_num = 0
    max_project_num = 25
    custom_settings = {
    'CONCURRENT_REQUESTS': 1
    }

    start_urls = ["http://sthjj.pds.gov.cn/channels/11330.html"]
    

    def parse(self, response):
        # Extract project links from the project list page
        project_links = response.xpath("//div[@class='xxgk']//tr[position()>1]//a/@href").getall()
        

        
        for link in project_links:
            self.current_project_num += 1
            yield scrapy.Request(response.urljoin(link), callback=self.parse_project,  meta={'project_num': self.current_project_num}, priority= 0)


        next_page = response.xpath("//a[contains(.,'下一页')]/@href").get()
        if next_page and self.current_project_num < self.max_project_num:
            yield scrapy.Request(next_page, callback=self.parse, priority= 1)
           

    def parse_project(self, response):
        # Create a folder for the project
        project_num = int(response.meta['project_num'])
        if project_num > self.max_project_num:
            return
        project_name = response.xpath("string(//div[@class='xxgkTable']/following-sibling::h1)").get()
        project_folder = f"sthjj/project{project_num}"
        os.makedirs(project_folder, exist_ok=True)

        # Save the subpage as an HTML file
        html_file = f"{project_folder}/page.html"
        with open(html_file, "wb") as file:
            file.write(response.body)

        # Extract specific content and save as a JSON file
        date = response.xpath("//div[@class = 'page-date']/text()[1]").get()
        date = re.search(r"\d{4}-\d{2}-\d{2}", date).group()
        json_file = f"{project_folder}/Meta Information.json"
        with open(json_file, "w") as file:
            json.dump(
                {
                    "Title of the page": project_name, 
                    "Date": date
                    }, 
                    file,
                    ensure_ascii= False,
                    indent=4
            )
    
        # Extract attachments and save as a ZIP folder
        zip_url = response.xpath("//div[@class = 'article']/p/a[not(contains(@href,'baidu'))]/@href").getall()
        zip_title = response.xpath("//div[@class = 'article']/p/a[not(contains(@href,'baidu'))]/@title").getall()        
        if zip_url:
            zip_folder = f"{project_folder}/Zip"
            os.makedirs(zip_folder, exist_ok=True)
            #download zip file
        for url, title in zip(zip_url, zip_title):
            yield scrapy.Request(url, callback=self.save_zip, meta={'zip_folder': zip_folder, 'title': title})
        
    def save_zip(self, response):
        zip_folder = response.meta['zip_folder']
        title = response.meta['title']

        # Extract the zip file
        zip_file_path = os.path.join(zip_folder, title)
        with open(zip_file_path, "wb") as file:
            file.write(response.body)
            self.log(f"zip saved")
    