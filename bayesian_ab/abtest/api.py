from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import Campaign, Variant
from .utils import sim_page_visits
from .simulation import experiment


class ABResponse(APIView):

    """ API to collect responses from users.
    This API registers the impressions generated from page views 
    and is also used to register conversions.
    AJAX call to be made using Javascript in the A/B test page. 
    """

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
                return Response(
                    {'details':'Campaign not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            if campaign.active == False:
                return Response({'details':'Campaign is inactive'})

            try:
                variant = Variant.objects.get(
                    code=variant_code,
                    campaign=campaign,
                )
            except Variant.DoesNotExist:
                return Response(
                    {'details':'Variant not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            session_vars = request.session.get(campaign_code)
            if not session_vars:
                return Response(
                    {'details':'Unable to find session variables for campaign.'}, 
                    status=status.HTTP_404_NOT_FOUND
                ) 

            try:
                session_impressions = session_vars['i']
                session_conversions = session_vars['c']
            except:
                return Response(
                    {'details':'Unable to retrieve session impressions and conversions'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            ## Update variant impressions / conversions
            if campaign.allow_repeat:
                # When repeated impressions and conversions are allowed for 
                # The same user/session
                variant.impressions = variant.impressions + int(register_impression)
                variant.conversions = variant.conversions + int(register_conversion)
                variant.conversion_rate = variant.conversions / variant.impressions
                variant.save()
            else:
                # Not allowing repeated impressions / conversions

                if session_impressions == 1:
                    # Add to variant impressions as this is first impression
                    variant.impressions = variant.impressions + int(register_impression)
                if session_conversions == 0 and register_conversion:
                    # Add to variant conversions as this is first conversion
                    variant.conversions = variant.conversions + int(register_conversion)

                variant.conversion_rate = variant.conversions / variant.impressions
                variant.save()
                
            ## Update session impressions / conversions
            request.session[campaign_code]['i'] = session_impressions + int(register_impression)
            request.session[campaign_code]['c'] = session_conversions + int(register_conversion)
            request.session.modified = True

            return Response({'details':'Response registered'})

class SimPageVisitsAPI(APIView):

    def post(self, request, forma=None):

        serializer = SimPageVisitsSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            
            campaign_code = serializer.data.get('campaign_code')
            conversion_rates = serializer.data.get('conversion_rates',{})
            n = serializer.data.get('n', 1)
            algo = serializer.data.get('algo')

            if algo not in ['uniform', 'thompson', 'egreedy', 'UCB1']:
                return Response(
                    {'details':'Invalid algorithm provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                campaign = Campaign.objects.get(code=campaign_code)
            except Campaign.DoesNotExist:
                return Response(
                    {'details':'Campaign does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
            sim_page_visits(
                campaign, 
                conversion_rates=conversion_rates, 
                n=n, 
                algo=algo
            )

            return Response({'details':'Page visits simulated'})


class RunSimulation(APIView):

    def post(self, request, format=None):

        serializer = SimulationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            
            p1 = serializer.data.get('p1')
            p2 = serializer.data.get('p2')
            p3 = serializer.data.get('p3')
            algo = serializer.data.get('algo')
            eps = serializer.data.get('eps', 0.1)

            if algo not in ['uniform', 'thompson', 'egreedy', 'UCB1']:
                return Response(
                    {'details':'Invalid algorithm provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = experiment(
                p1=p1,
                p2=p2,
                p3=p3,
                N=10000,
                algo=algo,
                eps=eps,
            )  

            return Response(data)
