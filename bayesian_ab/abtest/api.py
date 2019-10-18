from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import Campaign, Variant


class ABResponse(APIView):

    def post(self, request, format=None):

        serializer = ABResponseSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            campaign_code = serializer.data.get('campaign_code')
            variant_code = serializer.data.get('variant_code')
            register_impression = serializer.data.get('register_impression')
            register_conversion = serializer.data.get('register_conversion')
            params = serializer.data.get('params')

            try:
                campaign = Campaign.objects.get(code=campaign_code)
            except Campaign.DoesNotExist:
                return Response({'details':'Campaign not found'}, status=status.HTTP_404_NOT_FOUND)

            if campaign.active == False:
                return Response({'details':'Campaign is inactive'})

            try:
                variant = Variant.objects.get(
                    code=variant_code,
                    campaign=campaign,
                )
            except Variant.DoesNotExist:
                return Response({'details':'Variant not found'}, status=status.HTTP_404_NOT_FOUND)

            
            session_vars = request.session.get(campaign_code)
            if not session_vars:
                return Response({'details':'Unable to find session variables for campaign.'}, status=status.HTTP_404_NOT_FOUND) 

            try:
                session_impressions = session_vars['i']
                session_conversions = session_vars['c']
            except:
                return Response({'details':'Unable to retrieve session impressions and conversions'}, status=status.HTTP_404_NOT_FOUND)

            ## Update variant impressions / conversions
            if campaign.allow_repeat:
                # When repeated impressions and conversions are allowed for 
                # The same user/session
                variant.impressions = variant.impressions + int(register_impression)
                variant.conversions = variant.conversions + int(register_conversion)
                variant.save()
            else:
                # Not allowing repeated impressions / conversions

                if session_impressions == 1:
                    # Add to variant impressions as this is first impression
                    variant.impressions = variant.impressions + int(register_impression)
                if session_conversions == 0 and register_conversion:
                    # Add to variant conversions as this is first conversion
                    variant.conversions = variant.conversions + int(register_conversion)

            ## Update session impressions / conversions
            request.session[campaign_code]['i'] = session_impressions + int(register_impression)
            request.session[campaign_code]['c'] = session_conversions + int(register_conversion)
            request.session.modified = True

            return Response({'details':'Response registered'})





# class CategoryProductsAPI(CorpAPIView):

#     def get(self,request, url_path, format=None):

#         page = self.request.GET.get('page','1')

#         if not page.isdigit() :
#             page = 1 #if invalid / negative page number - default to 1

#         pricebook = request.user.user_profile.pricebook

#         try:
#             category = Category.objects.get(url_path=url_path)
#         except Category.DoesNotExist:
#             return Response({"details":"Category does not exist"}, status=status.HTTP_404_NOT_FOUND)

#         response = get_category_products(
#             category=category,
#             pricebook=pricebook,
#             page=page
#         )

#         response['cateogry_name'] = category.name
#         response['user_profile'] = self.user_profile

#         return Response(response)