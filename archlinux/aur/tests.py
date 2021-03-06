from datetime import datetime
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.template import Template, Context

from aur.forms import PackageSearchForm
from aur.models import Package, PackageNotification, Vote

class AurTestCase(TestCase):
    fixtures = ['test/users', 'test/packages']


class AurViewTests(AurTestCase):
    def test_index_view(self):
        response = self.client.get(reverse('aur-main'))
        self.assertEqual(response.status_code, 200)

    def test_search_view(self):
        response = self.client.get(reverse('aur-search'))
        self.assertEqual(response.status_code, 200)

        # Results with only one hit should redirect to package immediately
        response = self.client.get(reverse('aur-search'), data={
            'query': 'unique',
        })
        self.assertRedirects(response, reverse('aur-package_detail', kwargs={
            'slug': 'unique_package',
        }))

    def test_submit_view(self):
        self.client.login(username='normal_user', password='normal_user')
        response = self.client.get(reverse('aur-submit_package'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_package_view(self):
        response = self.client.get(reverse('aur-package_detail', kwargs={
            'slug': 'unique_package',
        }))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('aur-package_detail', kwargs={
            'slug': 'DoesNotExist',
        }))
        self.assertEqual(response.status_code, 404)

    def test_vote_view(self):
        user = User.objects.get(username='normal_user')
        package = Package.objects.get(name='unique_package')
        self.client.login(username=user.username, password='normal_user')
        response = self.client.get(reverse('aur-vote', kwargs={
            'slug': package.slug,
        }))
        self.assertRedirects(response, reverse('aur-package_detail', kwargs={
            'slug': package.slug,
        }))
        self.assertEqual(user.vote_set.count(), 1)
        self.assertEqual(package.vote_set.count(), 1)
        response = self.client.get(reverse('aur-vote', kwargs={
            'slug': 'DoesNotExist',
        }))
        self.assertEqual(response.status_code, 404)
        # Make sure that we didn't count a vote for a nonexistent package...
        self.assertEqual(user.vote_set.count(), 1)

    def test_unvote_view(self):
        package = Package.objects.get(name='unique_package')
        user = User.objects.get(username='normal_user')
        Vote(package=package, user=user).save()
        self.client.login(username=user.username, password='normal_user')
        response = self.client.get(reverse('aur-unvote', kwargs={
            'slug': package.slug,
        }))
        self.assertRedirects(response, reverse('aur-package_detail', kwargs={
            'slug': package.slug,
        }))
        self.assertEqual(package.vote_set.count(), 0)
        self.assertEqual(user.vote_set.count(), 0)
        response = self.client.get(reverse('aur-unvote', kwargs={
            'slug': 'DoesNotExist',
        }))
        self.assertEqual(response.status_code, 404)

class AurAPITests(AurTestCase):
    def test_search_view(self):
        response = self.client.get(reverse('aur.views.api_search', kwargs={
            'query': 'package',
            'format': 'json',
        }))
        self.assertEqual(response.status_code, 200)

    def test_package_view(self):
        response = self.client.get(reverse('aur.views.api_package_info', kwargs={
            'object_id' :'unique_package',
            'format': 'json',
        }))
        self.assertEqual(response.status_code, 200)

        # Requested package does not exist (404)
        response = self.client.get(reverse('aur.views.api_package_info', kwargs={
            'object_id' :'DoesNotExist',
            'format': 'json',
        }))
        self.assertEqual(response.status_code, 404)


class AurModelTests(AurTestCase):
    def test_update_notification(self):
        user = User.objects.get(username='normal_user')
        package = Package.objects.get(name='unique_package')
        PackageNotification(package=package, user=user).save()
        # Update version and save
        package.version = unicode(float(package.version) + 1)
        package.save()
        # Check that the mail was sent out
        self.assertEquals(len(mail.outbox), 1)

    def test_delete_notification(self):
        user = User.objects.get(username='normal_user')
        package = Package.objects.get(name='unique_package')
        PackageNotification(package=package, user=user).save()
        package.delete()
        # Check that the mail was sent out
        # FIXME: This currently fails because tarball doesn't actually exist,
        # and its removal is attempted
        self.assertEquals(len(mail.outbox), 1)

class AurFormTests(AurTestCase):
    def test_search_form(self):
        form = PackageSearchForm(data={
            'query': 'unique_package'
        })
        self.failUnless(form.is_valid())
        results = form.search()
        self.assertEquals(results.count(), 1)
        self.assertEquals(results[0].name, 'unique_package')


class AurTemplateTagTests(AurTestCase):
    def test_has_update_notification(self):
        user = User.objects.get(username='normal_user')
        package = Package.objects.get(name='unique_package')
        context = Context({
            'user': user,
            'package': package,
        })
        template = Template("""
            {% load aur_tags %}
            {% if user|has_update_notification:package %}
                True
            {% else %}
                False
            {% endif %}
        """)
        self.assertEquals(template.render(context).strip(), "False")
        PackageNotification(package=package, user=user).save()
        self.assertEquals(template.render(context).strip(), "True")

    def test_has_vote(self):
        user = User.objects.get(username='normal_user')
        package = Package.objects.get(name='unique_package')
        context = Context({
            'user': user,
            'package': package,
        })
        template = Template("""
            {% load aur_tags %}
            {% if user|has_vote:package %}
                True
            {% else %}
                False
            {% endif %}
        """)
        self.assertEquals(template.render(context).strip(), "False")
        Vote(package=package, user=user).save()
        self.assertEquals(template.render(context).strip(), "True")

