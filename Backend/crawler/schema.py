link_schema = {
    "name": "Amazon_test",
    "baseSelector": "//div[@data-asin and @role]",
    "fields": [
        {
            "name": "hyperlink",
            "selector": ".//a",
            "type": "attribute",
            "attribute": "href"
        }
    ]
}

data_schema = {
        "name": "Amazon_test",
        "baseSelector": "//div[@id='dp']/div[@id='dp-container']",
        "fields": [
            {
                "name": "asin",
                "selector": "./div[@id='ppd']/div[@id='centerCol']/div[@id='averageCustomerReviews_feature_div']/div[@id='averageCustomerReviews' and @data-asin]",
                "type": "attribute",
                "attribute": "data-asin"
            },
            {
                "name": "title",
                "selector": "./div[@id='ppd']/div[@id='centerCol']//span[@id='productTitle']",
                "type": "text"
            },
            {
                "name": "brand",
                "selector": "./div[@id='ppd']/div[@id='centerCol']/div[@id='productOverview_feature_div']//tr[@class='a-spacing-small po-brand']/td[@class='a-span9']/span",
                "type": "text"
            },
            {
                "name": "rating",
                "selector": "./div[@id='ppd']/div[@id='centerCol']/div[@id='averageCustomerReviews_feature_div']/div[@id='averageCustomerReviews' and @data-asin]//a//span[@aria-hidden]",
                "type": "text"
            },
            {
                "name": "rating_count",
                "selector": ".//div[@id='averageCustomerReviews']//span[@id='acrCustomerReviewText']",
                "type": "text"
            },
            {
                "name": "price",
                "selector": ".//div[@id='corePriceDisplay_desktop_feature_div']//span[@class='aok-offscreen']",
                "type": "text"
            },
            {
                "name": "info",
                "selector": ".//div[@id='feature-bullets']//ul",
                "type": "text"
            },
            {
                "name": "availability",
                "selector": ".//div[@id='availability']//span",
                "type": "text"
            },
            {
                "name": "product_description",
                "selector": ".//div[@id='productDescription']//span",
                "type": "text"
            },
            {
                "name": "return_policy",
                "selector": ".//div[@id='offer-display-features']//div[@id='returnsInfoFeature_feature_div']/div[@data-csa-c-content-id='desktop-return-info' and @offer-display-feature-name='desktop-return-info']/span",
                "type": "text"
            },
            {
                "name": "images",
                "selector": ".//div[@id='imageBlock']//li[@data-csa-c-element-type='navigational']",
                "type": "list",
                "fields": [
                    {
                        "name": "src",
                        "selector": ".//span[@aria-hidden]/img",
                        "type": "attribute",
                        "attribute": "src"
                    }
                ]
            }
        ]
    }