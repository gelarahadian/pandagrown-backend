from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import user, activity, profile, benefit_history, ticket
from websocket_app.views import NotificationsListAPIView

router_ticket_depart = DefaultRouter()
router_ticket_depart.register(r'', ticket.TicketDepartmentViewSet)

router_ticket = DefaultRouter()
router_ticket.register(r'', ticket.TicketViewSet)

router_user_agent = DefaultRouter()
router_user_agent.register(r'', user.UserAgentViewSet)

urlpatterns = [
    # user
    path('manage/', user.UserListView.as_view(), name="user-list"),
    path('support/manage/', user.UserListSupportView.as_view(), name="user-support-list"),
    path('manage/<int:pk>/update/', user.UserUpdateView.as_view(), name="user-update-page"),
    path('manage/<int:pk>/delete/', user.UserDeleteView.as_view(), name="user-delete-page"),
    path('<int:user_id>/referr/link/', user.ReferrLinkView.as_view(), name='user-referrer-link'),
    path('<int:user_id>/referr/email/', user.ReferrEmailView.as_view(), name='user-referr-email'),
    path('<int:user_id>/referrs/', user.ReferrsView.as_view(), name='user-referrs'),

    # UserActivity
    path('activity/', activity.UserActivityListView.as_view(), name="user-activity-list"),
    path('<int:user_id>/activity/', activity.UserActivityListView.as_view(), name="user-activity-list"),
    path('<int:user_id>/activity/create/', activity.UserActivityCreateView.as_view(), name="user-activity-create"),
    path('<int:user_id>/activity/<int:pk>/', activity.UserActivityDetailView.as_view(), name="user-activity-detail"),
    path('<int:user_id>/activity/<int:pk>/update/', activity.UserActivityUpdateView.as_view(), name="user-activity-update"),
    path('<int:user_id>/activity/<int:pk>/delete/', activity.UserActivityDeleteView.as_view(), name="user-activity-delete"),

    # UserProfile
    path('<int:user_id>/profile/', profile.UserProfileListView.as_view(), name="user-profile-list"),
    path('<int:user_id>/profile/balance/', profile.UserProfileBalanceView.as_view(), name="user-balance-list"),
    path('<int:user_id>/profile/create/', profile.UserProfileCreateView.as_view(), name="user-profile-create"),
    path('<int:user_id>/profile/<int:pk>/', profile.UserProfileDetailView.as_view(), name="user-profile-detail"),
    path('<int:user_id>/profile/<int:pk>/update/', profile.UserProfileUpdateView.as_view(), name="user-profile-update"),
    path('<int:user_id>/profile/<int:pk>/delete/', profile.UserProfileDeleteView.as_view(), name="user-profile-delete"),
    
    # BenefitHistory
    path('benefit/', benefit_history.BenefitHistoryListView.as_view(), name="benefit-list-page"),
    path('<int:user_id>/benefit/', benefit_history.BenefitHistoryListView.as_view(), name="benefit-list-page"),
    path('<int:user_id>/benefit/<int:pk>/', benefit_history.BenefitHistoryDetailView.as_view(), name="benefit-detail-page"),
    path('<int:user_id>/benefit/create/', benefit_history.BenefitHistoryCreateView.as_view(), name="benefit-create-page"),
    path('<int:user_id>/benefit/<int:pk>/update/', benefit_history.BenefitHistoryUpdateView.as_view(), name="benefit-update-page"),
    path('<int:user_id>/benefit/<int:pk>/delete/', benefit_history.BenefitHistoryDeleteView.as_view(), name="benefit-delete-page"),

    path('<int:user_id>/notifications/', NotificationsListAPIView.as_view(), name='notifications-list'),
    # Ticket
    path('ticket/status/<int:ticket_id>/', ticket.TicketStatusUpdateView.as_view(), name='ticket-status-update'),
    path('ticket/reply/', ticket.ReplyTicketView.as_view(), name='ticket-reply'),
    path('ticket/reply/<int:ticket_id>/', ticket.ReplyTicketListView.as_view(), name='ticket-admin-reply-list'),
    path('<int:user_id>/ticket/reply/<int:ticket_id>/', ticket.ReplyTicketListView.as_view(), name='ticket-user-reply-list'),
    path('ticket/generate/id/', ticket.GenerateTicketIdView.as_view(), name='ticket-generate-id'),
    path('ticket/department/', include(router_ticket_depart.urls)),
    path('ticket/', include(router_ticket.urls)),

    # Report
    path('<int:user_id>/report/', user.UserReportView.as_view(), name='user-report-view'),

    path('<int:user_id>/status/', profile.GetStatusView.as_view(), name='get-user-status'),
    path('agent/', include(router_user_agent.urls), name='user-agent'),
    path('agent/<int:pk>/delete/', include(router_user_agent.urls), name="user-agent-delete"),
]