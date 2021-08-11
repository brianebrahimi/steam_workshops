import scrapy
from scrapy import Request, FormRequest
from scrapy.item import Item, Field
from scrapy.loader import ItemLoader
import json
from scrapy import Selector
import re
from datetime import datetime


class Workshop_Item(Item):
    app_id = Field()
    workshop_id = Field()
    game = Field()
    workshop_name = Field()
    user = Field()
    comment = Field()
    user_level = Field()
    date_posted = Field()
    user_location = Field()
    number_of_badges = Field()
    user_join_date = Field()
    is_author = Field()
    user_experience = Field()
    aliases = Field()
    comment_date_posted = Field()
    comment_time_posted = Field()


class Workshop_Comment_Spider(scrapy.Spider):
    name = "comments"
    with open("output/workshop_comment_links.txt") as f:
        urls = [line.rstrip("\n") for line in f]
    start_urls = urls

    def parse(self, response):
        #if more than 0 comments, the workshop creators id number is saved
        if int(max(response.css('span.tabCount::text').getall())) > 0:
            contributor_id = re.search(r'Public_(.*?)_' , response.css('div.commentthread_footer a::attr(id)').get()).group(1)

        workshop_id_number = response.css('form.smallForm > input::attr(value)').get()

        if max(list(map(int, response.css('span.tabCount::text').getall()))) > 50:
            comment_number = str(max(list(map(int, response.css('span.tabCount::text').getall()))))

            url = f'https://steamcommunity.com/comment/PublishedFile_Public/render/{contributor_id}/{workshop_id_number}/'
            data = {
                "start": "0",
                "totalcount": comment_number,
                "count": comment_number,
                "sessionid": "d880ab2338b70926db0a9591",
                "extended_data": "{\"contributors\":[\"" + contributor_id +"\",{}],\"appid\":289070,\"sharedfile\":{\"m_parentsDetails\":null,\"m_parentBundlesDetails\":null,\"m_bundledChildren\":[],\"m_ownedBundledItems\":[]},\"parent_item_reported\":false}",
                "feature2": "-1"
            }

            app_id = response.css('div.apphub_HeaderTop a::attr(data-appid)').get()
            game = response.css(".apphub_AppName::text").get()
            workshop_id = response.css('form.smallForm input::attr(value)').get()
            workshop_name = response.css(".workshopItemTitle::text").get()
            yield FormRequest(url, formdata=data, callback=self.parse_paginated_comments, meta={'app_id': app_id, 'game': game, 'workshop_id': workshop_id, 'workshop_name': workshop_name})


        else:

            for comment in response.css(".commentthread_comment.responsive_body_text"):
                item = Workshop_Item()
                item['is_author'] = False
                item['aliases'] = 'none'

                if "authorbadge" in comment.get():
                    item['is_author'] = True

                item['app_id'] = response.css('div.apphub_HeaderTop a::attr(data-appid)').get()
                item['workshop_id'] = response.css('form.smallForm input::attr(value)').get()
                item['game'] = response.css(".apphub_AppName::text").get()
                item['workshop_name'] = response.css(".workshopItemTitle::text").get()
                item['user'] = comment.css("bdi::text").get()
                item['comment'] = ",".join(comment.css(".commentthread_comment_text::text").getall()).replace('\n', ' ').replace('\t', '').replace('\r', ' ').replace(";", "")
                
                date_posted_list = comment.css(".commentthread_comment_timestamp::attr(title)").get().replace(",", "").replace(".", "").split(" ")
                date_posted_list_time = date_posted_list[4].split(":")
                if 'pm' in date_posted_list:
                    date_posted_list_time[0] = str(int(date_posted_list_time[0]) + 12)

                item['date_posted'] = date_posted_list[2] +"-"+ str(datetime.strptime(date_posted_list[0], "%B").month) +"-"+ date_posted_list[1][:2] +"T"+ date_posted_list_time[0] +":"+ date_posted_list_time[1] +":"+ date_posted_list_time[2]
                
                item['user_level'] = -1
                user_profile = comment.css(".commentthread_author_link::attr(href)").get()
                request = Request(user_profile, callback=self.parse_user_info, meta={'item': item})
                yield request

    def parse_user_info(self, response):
        item = response.meta['item']

        if response.css('.profile_private_info'):
            item['user_level'] = 'private'
            item['user_location'] = 'private'
            item['number_of_badges'] = 'private'
            item['user_join_date'] = 'private'
            item['user_experience'] = 'private'
            yield Request(response.request.url + "/ajaxaliases", callback=self.parse_aliases, meta={'item': item})
        else:
            item['user_level'] = response.css(".friendPlayerLevelNum::text").get()

            if response.css('.header_real_name') and response.css("img.profile_flag"):
                item['user_location'] = response.css('.header_real_name::text').getall()[2].strip()
            else:
                item['user_location'] = 'NA'

            if response.css("div.profile_badges span.profile_count_link_total::text"):
                item['number_of_badges'] = response.css("div.profile_badges span.profile_count_link_total::text").get().strip()
            else:
                item['number_of_badges'] = 'NA'

            user_badge_page = response.css("div.profile_header_badgeinfo_badge_area > a::attr(href)").get() + "/1"
            request = Request(user_badge_page, callback=self.parse_badge_info, meta={'item': item})
            yield request

    def parse_aliases(self, response):
        item = response.meta['item']
        jsonresponse = json.loads(response.text)
        item['aliases'] = []
        for name in jsonresponse:
            item['aliases'].append(name['newname'])
        if item['aliases'] == []:
            item['aliases'] = "NONE"

        item['comment_date_posted'] = item['date_posted'].split("T")[0]
        item['comment_time_posted'] = item['date_posted'].split("T")[1]
        del item['date_posted']
        yield item


    def parse_badge_info(self, response):
        item = response.meta['item']
        if "Years of Service" in response.css("title::text").get():
            user_join_date_list = response.css("div.badge_description::text").get().replace(",", "").replace(".", "").strip().split(" ")
            item['user_join_date'] = user_join_date_list[4] +"-"+ str(datetime.strptime(user_join_date_list[2], "%B").month) +"-"+ str(user_join_date_list[3])
        else:
            item['user_join_date'] = "NA"
        experience_page = response.css('a.whiteLink.persona_name_text_content::attr(href)').get() + "/badges"
        request = Request(experience_page, callback=self.parse_experience_page, meta={'item': item})
        yield request
        
    def parse_experience_page(self, response):
        item = response.meta['item']
        if response.css('span.profile_xp_block_xp'):
            item['user_experience'] = response.css('span.profile_xp_block_xp::text').get()
        yield Request(response.css("span.profile_small_header_name a::attr(href)").get() + "/ajaxaliases", callback=self.parse_aliases, meta={'item': item})

    def parse_paginated_comments(self, response):
        app_id = response.meta['app_id']
        game = response.meta['game']
        workshop_id = response.meta['workshop_id']
        workshop_name = response.meta['workshop_name']
        jsonresponse = json.loads(response.body.decode("utf-8"))
        sel = Selector(text=jsonresponse['comments_html'])
        for comment in sel.css(".commentthread_comment.responsive_body_text"):
            item = Workshop_Item()
            item['is_author'] = False


            if "authorbadge" in comment.get():
                item['is_author'] = True

            item['app_id'] = app_id #sel.css('div.apphub_HeaderTop a::attr(data-appid)').get()
            item['workshop_id'] = workshop_id #sel.css('form.smallForm input::attr(value)').get()
            item['game'] = game #sel.css(".apphub_AppName::text").get()
            item['workshop_name'] = workshop_name #sel.css(".workshopItemTitle::text").get()
            item['user'] = comment.css("bdi::text").get()
            item['comment'] = ",".join(comment.css(".commentthread_comment_text::text").getall()).replace('\n', ' ').replace('\t', '').replace('\r', ' ').replace(";", "")
           
            date_posted_list = comment.css(".commentthread_comment_timestamp::attr(title)").get().replace(",", "").replace(".", "").split(" ")
            date_posted_list_time = date_posted_list[4].split(":")
            if 'pm' in date_posted_list:
                date_posted_list_time[0] = str(int(date_posted_list_time[0]) + 12)

            item['date_posted'] = date_posted_list[2] +"-"+ str(datetime.strptime(date_posted_list[0], "%B").month) +"-"+ date_posted_list[1][:2] +"T"+ date_posted_list_time[0] +":"+ date_posted_list_time[1] +":"+ date_posted_list_time[2]
            
            item['user_level'] = -1
            user_profile = comment.css(".commentthread_author_link::attr(href)").get()
            request = Request(user_profile, callback=self.parse_user_info, meta={'item': item})
            yield request