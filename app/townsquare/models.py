from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

from economy.models import SuperModel


class Like(SuperModel):
    """A like is an indication of a favored activity feed item"""

    profile = models.ForeignKey('dashboard.Profile',
        on_delete=models.CASCADE, related_name='likes', blank=True)
    activity = models.ForeignKey('dashboard.Activity',
        on_delete=models.CASCADE, related_name='likes', blank=True, db_index=True)

    def __str__(self):
        return f"Like of {self.activity.pk} by {self.profile.handle}"

    @property
    def url(self):
        return self.activity.url

    def get_absolute_url(self):
        return self.activity.url


class Flag(SuperModel):
    """A Flag is an indication of a flagged activity feed item"""

    profile = models.ForeignKey('dashboard.Profile',
        on_delete=models.CASCADE, related_name='flags', blank=True)
    activity = models.ForeignKey('dashboard.Activity',
        on_delete=models.CASCADE, related_name='flags', blank=True, db_index=True)

    def __str__(self):
        return f"Flag of {self.activity.pk} by {self.profile.handle}"

    @property
    def url(self):
        return self.activity.url

    def get_absolute_url(self):
        return self.activity.url


class Comment(SuperModel):
    """An comment on an activity feed item"""

    profile = models.ForeignKey('dashboard.Profile',
        on_delete=models.CASCADE, related_name='comments', blank=True)
    activity = models.ForeignKey('dashboard.Activity',
        on_delete=models.CASCADE, related_name='comments', blank=True, db_index=True)
    comment = models.TextField(default='', blank=True)

    def __str__(self):
        return f"Comment of {self.activity.pk} by {self.profile.handle}: {self.comment}"

    @property
    def profile_handle(self):
        return self.profile.handle

    @property
    def tip_able(self):
        return self.activity.metadata.get("tip_able", False)

    @property
    def url(self):
        return self.activity.url

    @property
    def tip_count_eth(self):
        from dashboard.models import Tip
        network = 'rinkeby' if settings.DEBUG else 'mainnet'
        tips = Tip.objects.filter(comments_priv=f"comment:{self.pk}", network=network)
        return sum([tip.value_in_eth for tip in tips])

    def get_absolute_url(self):
        return self.url


@receiver(post_save, sender=Comment, dispatch_uid="post_save_comment")
def postsave_comment(sender, instance, created, **kwargs):
    from marketing.mails import comment_email
    comment_email(instance)
    print("SENT EMAIL")


class OfferQuerySet(models.QuerySet):
    """Handle the manager queryset for Offers."""

    def current(self):
        """Filter results down to current offers only."""
        return self.filter(valid_from__lte=timezone.now(), valid_to__gt=timezone.now(), public=True)

num_backgrounds = 33


class Offer(SuperModel):
    """An offer"""
    OFFER_TYPES = [
        ('secret', 'secret'),
        ('random', 'random'),
        ('daily', 'daily'),
        ('weekly', 'weekly'),
        ('monthly', 'monthly'),
        ('other', 'other'),
    ]
    STYLES = [
        ('red', 'red'),
        ('green', 'green'),
        ('blue', 'blue'),
    ] + [(f'back{i}', f'back{i}') for i in range(0, num_backgrounds + 1)]

    from_name = models.CharField(max_length=50, blank=True)
    from_link = models.URLField(blank=True)
    title = models.TextField(default='', blank=True)
    desc = models.TextField(default='', blank=True)
    url = models.URLField(db_index=True)
    valid_from = models.DateTimeField(db_index=True)
    valid_to = models.DateTimeField(db_index=True)
    key = models.CharField(max_length=50, db_index=True, choices=OFFER_TYPES)
    style = models.CharField(max_length=50, db_index=True, choices=STYLES, default='announce1')
    persona = models.ForeignKey('kudos.Token', blank=True, null=True, related_name='offers', on_delete=models.SET_NULL)
    created_by = models.ForeignKey('dashboard.Profile',
        on_delete=models.CASCADE, related_name='offers_created', blank=True, null=True)
    public = models.BooleanField(help_text='Is this available publicly yet?', default=True)
    view_count = models.IntegerField(default=0, db_index=True)

    # Bounty QuerySet Manager
    objects = OfferQuerySet.as_manager()

    def __str__(self):
        return f"{self.key} / {self.title}"

    @property
    def view_url(self):
        slug = slugify(self.title)
        return f'/action/{self.pk}/{slug}'

    def get_absolute_url(self):
        return self.view_url + '?preview=1'

    @property
    def go_url(self):
        return self.view_url + '/go'

    @property
    def decline_url(self):
        return self.view_url + '/decline'


class OfferAction(SuperModel):
    """An offer action, where a click or a completion"""

    profile = models.ForeignKey('dashboard.Profile',
        on_delete=models.CASCADE, related_name='offeractions', blank=True)
    offer = models.ForeignKey('townsquare.Offer',
        on_delete=models.CASCADE, related_name='actions', blank=True)
    what = models.CharField(max_length=50, db_index=True) # click, completion, etc

    def __str__(self):
        return f"{self.profile.handle} => {self.what} => {self.offer.title}"


class AnnounceQuerySet(models.QuerySet):
    """Handle the manager queryset for Announcements."""

    def current(self):
        """Filter results down to current offers only."""
        return self.filter(valid_from__lte=timezone.now(), valid_to__gt=timezone.now())


class Announcement(SuperModel):
    """An Announcement to the users to be displayed on town square."""

    _TYPES = [
        ('townsquare', 'townsquare'),
        ('header', 'header'),
        ('footer', 'footer'),
    ]
    key = models.CharField(max_length=50, db_index=True, choices=_TYPES)
    title = models.TextField(default='', blank=True)
    desc = models.TextField(default='', blank=True)
    valid_from = models.DateTimeField(db_index=True)
    valid_to = models.DateTimeField(db_index=True)
    rank = models.IntegerField(default=0)

    STYLES = [
        ('primary', 'primary'),
        ('secondary', 'secondary'),
        ('success', 'success'),
        ('danger', 'danger'),
        ('warning', 'warning'),
        ('info', 'info'),
        ('light', 'light'),
        ('dark', 'dark'),
        ('white', 'white'),
    ]

    style = models.CharField(max_length=50, db_index=True, choices=STYLES, default='announce1', help_text='https://getbootstrap.com/docs/4.0/utilities/colors/')

    # Bounty QuerySet Manager
    objects = AnnounceQuerySet.as_manager()
    def __str__(self):
        return f"{self.created_on} => {self.title}"
