import scrapy
import os
import json
import zipfile
import io


class uvpSpider(scrapy.Spider):
    name = "uvp_spider"
    current_project_num = 0
    max_project_num = 25
    custom_settings = {
    'CONCURRENT_REQUESTS': 1
    }

    start_urls = ["https://www.uvp-verbund.de/freitextsuche?rstart=0&currentSelectorPage=1"]
    

    def parse(self, response):
        # Extract project links from the project list page
        project_links = response.xpath("//div[@class= 'teaser-data search']/a[1]/@href").getall()
        

        
        for link in project_links:
            self.current_project_num += 1
            yield scrapy.Request(response.urljoin(link), callback=self.parse_project,  meta={'project_num': self.current_project_num}, priority= 0)


        last_page = response.xpath("//span[@class = 'ic-ic-arrow-right']/parent::a/preceding-sibling::a[1]/@href").get()
        next_page = response.xpath("//span[@class = 'ic-ic-arrow-right']/parent::a/@href").get()
        if last_page and self.current_project_num < self.max_project_num:
            yield scrapy.Request(next_page, callback=self.parse, priority= 1)
           

    def parse_project(self, response):
        # Create a folder for the project
        project_num = int(response.meta['project_num'])
        if project_num > self.max_project_num:
            return
        project_name = response.xpath("//h1//text()").get().strip()
        project_folder = f"uvp/project{project_num}"
        os.makedirs(project_folder, exist_ok=True)

        # Save the subpage as an HTML file
        html_file = f"{project_folder}/page.html"
        with open(html_file, "wb") as file:
            file.write(response.body)

        # Extract specific content and save as a JSON file
        date = response.xpath("//div[@class='helper text date']/span//text()").get().strip()
        description = response.xpath("string(//h3[contains(.,'Allgemeine Vorhabenbeschreibung')]/following-sibling::p[1])").getall()
        json_file = f"{project_folder}/Meta Information.json"
        with open(json_file, "w") as file:
            json.dump(
                {
                    "Title of the page": project_name, 
                    "Date": date, 
                    "General Project Description": description
                    }, 
                    file,
                    ensure_ascii= False,
                    indent=4
            )

        # Extract attachments and save as a ZIP folder
        zip_url = response.xpath("//div[@class= 'zip-download']//a/@href").get()
        if zip_url:
            zip_folder = f"{project_folder}/Zip"
            os.makedirs(zip_folder, exist_ok=True)
            #download zip file
            yield scrapy.Request(response.urljoin(zip_url), callback=self.save_zip, meta={'zip_folder': zip_folder})
        
    def save_zip(self, response):
        zip_folder = response.meta['zip_folder']

        # Extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.body)) as zip_ref:
            zip_ref.extractall(zip_folder)
            self.log(f"zip saved")
