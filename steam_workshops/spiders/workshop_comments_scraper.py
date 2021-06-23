import scrapy
from scrapy import Request
from scrapy.item import Item, Field
from scrapy.loader import ItemLoader


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


class Workshop_Comment_Spider(scrapy.Spider):
    name = "comments"
    with open("output/workshop_comment_links.txt") as f:
        urls = [line.rstrip("\n") for line in f]
    start_urls = urls

    def parse(self, response):
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
            yield request

    def parse_user_info(self, response):
        item = response.meta['item']
        if response.css('.profile_private_info'):
            item['user_level'] = 'private'
            item['user_location'] = 'private'
            item['number_of_badges'] = 'private'
            item['user_join_date'] = 'private'
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
        return item
