import scrapy
from scrapy import Request, FormRequest
from scrapy.item import Item, Field
from scrapy.loader import ItemLoader
import json
from scrapy import Selector


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


class Workshop_Comment_Spider(scrapy.Spider):
    name = "comments"
    with open("output/workshop_comment_links.txt") as f:
        urls = [line.rstrip("\n") for line in f]
    start_urls = urls

    def parse(self, response):
        if int(response.css('span.tabCount::text').getall()[1]) > 0 and "profiles" in response.css('a.commentthread_author_link::attr(href)').get():
            contributor_id = re.search(r'profiles/(.*?)' , response.css('a.commentthread_author_link::attr(href)').get()).group(1)
        elif int(response.css('span.tabCount::text').getall()[1]) > 0:
            contributor_id = re.search(r'id/(.*?)' , response.css('a.commentthread_author_link::attr(href)').get()).group(1)
        workshop_id_number = response.css('form.smallForm > input::attr(value)').get()

        if int(response.css('span.tabCount::text').getall()[1]) > 50:

            comment_number = response.css('span.tabCount::text').getall()[1]
            print(contributor_id, " $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

            url = f'https://steamcommunity.com/comment/PublishedFile_Public/render/{contributor_id}/{workshop_id_number}/'

            headers = {
                'Accept':   'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding':  'gzip, deflate, br',
                'Accept-Language':  'en-US,en;q=0.5',
                'Connection':   'keep-alive',
                'Host': 'steamcommunity.com',
                'Upgrade-Insecure-Requests':    '1',
                'User-Agent':   'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'
            }

            data = {
                "start": "1",
                "totalcount": comment_number,
                "count": comment_number,
                "sessionid": "d880ab2338b70926db0a9591",
                f"extended_data": "{\"contributors\":[\"{contributor_id}\",{}],\"appid\":289070,\"sharedfile\":{\"m_parentsDetails\":null,\"m_parentBundlesDetails\":null,\"m_bundledChildren\":[],\"m_ownedBundledItems\":[]},\"parent_item_reported\":false}",
                "feature2": "-1"
            }

            yield FormRequest(url, formdata=data, callback=self.parse_paginated_comments, dont_filter=True,)


        '''else:
            for comment in response.css(".commentthread_comment"):
                item = Workshop_Item()
                item['is_author'] = False

                if "authorbadge" in comment.get():
                    item['is_author'] = True

                item['app_id'] = response.css('div.apphub_HeaderTop a::attr(data-appid)').get()
                item['workshop_id'] = response.css('form.smallForm input::attr(value)').get()
                item['game'] = response.css(".apphub_AppName::text").get()
                item['workshop_name'] = response.css(".workshopItemTitle::text").get()
                item['user'] = comment.css("bdi::text").get()
                item['comment'] = ",".join(comment.css(".commentthread_comment_text::text").getall()).replace('\n', ' ').replace('\t', '').replace('\r', ' ')
                item['date_posted'] = comment.css(".commentthread_comment_timestamp::attr(title)").get()
                item['user_level'] = -1
                user_profile = comment.css(".commentthread_author_link::attr(href)").get()
                request = Request(user_profile, callback=self.parse_user_info, meta={'item': item})
                yield request'''

    def parse_user_info(self, response):
        item = response.meta['item']
        if response.css('.profile_private_info'):
            item['user_level'] = 'private'
            item['user_location'] = 'private'
            item['number_of_badges'] = 'private'
            item['user_join_date'] = 'private'
            item['user_experience'] = 'private'
            return item
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

    def parse_badge_info(self, response):
        item = response.meta['item']
        if response.css("div.badge_description"):
            item['user_join_date'] = response.css("div.badge_description::text").get().strip()
        experience_page = response.css('a.whiteLink.persona_name_text_content::attr(href)').get() + "/badges"
        request = Request(experience_page, callback=self.parse_experience_page, meta={'item': item})
        yield request
        
    def parse_experience_page(self, response):
        item = response.meta['item']
        if response.css('span.profile_xp_block_xp'):
            item['user_experience'] = response.css('span.profile_xp_block_xp::text').get()
        return item

    def parse_paginated_comments(self, response):
        print("$$$$$############################################################################################################################################################")
        jsonresponse = json.loads(response.body.decode("utf-8"))
        print(jsonresponse)
        sel = Selector(text=jsonresponse['comments_html'])

        for comment in sel.css(".commentthread_comment"):
            item = Workshop_Item()
            item['is_author'] = False

            if "authorbadge" in comment.get():
                item['is_author'] = True

            item['app_id'] = response.css('div.apphub_HeaderTop a::attr(data-appid)').get()
            item['workshop_id'] = response.css('form.smallForm input::attr(value)').get()
            item['game'] = response.css(".apphub_AppName::text").get()
            item['workshop_name'] = response.css(".workshopItemTitle::text").get()
            item['user'] = comment.css("bdi::text").get()
            item['comment'] = ",".join(comment.css(".commentthread_comment_text::text").getall()).replace('\n', ' ').replace('\t', '').replace('\r', ' ')
            item['date_posted'] = comment.css(".commentthread_comment_timestamp::attr(title)").get()
            item['user_level'] = -1
            user_profile = comment.css(".commentthread_author_link::attr(href)").get()
            request = Request(user_profile, callback=self.parse_user_info, meta={'item': item})
            yield request