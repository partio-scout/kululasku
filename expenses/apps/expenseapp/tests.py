from http import HTTPStatus
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile


from .models import ExpenseType, Organisation, Person


class TestNewExpenseFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jacob.tester', email='jacob@partio.fi', password='top_secret', first_name='Jacob', last_name='Tester')
        self.person = Person.objects.get_or_create(
            user=self.user, type=1, address='Testitie 123', personno='010101-123N', iban='GB33BUKB20201555555555')
        self.organisation = Organisation.objects.create(
            name="Turun Hiihtäjät ry", business_id="y-1234", active=True, send_active=True)

    def test_fail_login(self):
        response = self.client.post(
            "/accounts/login/", data={"username": "jacob.tester",
                                      "password": "not_working_password",
                                      })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, "Sisäänkirjautuminen epäonnistui."
        )

    def test_success_login(self):
        self.client.login(username='jacob.tester', password='top_secret',
                          name='Jacob Tester', address='Kotitie 112')
        response = self.client.get(
            "/expense/")

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertContains(
            response, "Valitse organisaatiosi"
        )

    def test_user_can_edit_person(self):
        self.client.login(username='jacob.tester', password='top_secret')
        response = self.client.get(
            f"/personinfo/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Käyttäjätiedot'
        )

        postResponse = self.client.post(f"/personinfo/", data={
            "firstname": "Jaakop",
            "lastname": "Tester",
            "email": "jacob@partio.fi",
            "personno": "",
            "address": "",
            "phone": "",
            "iban": "",
            "swift_bic": "",
            "type": 1,
            "language": "fi-FI"
        })

        self.assertEqual(postResponse.status_code, HTTPStatus.OK)
        self.assertContains(
            postResponse, 'Profiilitiedot päivitetty'
        )

    def test_user_edit_validation_works(self):
        self.client.login(username='jacob.tester', password='top_secret')
        response = self.client.get(
            f"/personinfo/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Käyttäjätiedot'
        )

        postResponse = self.client.post(f"/personinfo/", data={
            "firstname": "Jaakop",
            "lastname": "Tester",
            "email": "",
            "personno": "",
            "address": "",
            "phone": "",
            "iban": "",
            "swift_bic": "",
            "type": 1,
            "language": "fi-FI"
        })

        self.assertEqual(postResponse.status_code, HTTPStatus.OK)
        self.assertContains(
            postResponse, 'Tarkista että kaikki tiedot ovat oikein.'
        )

    def test_user_create_expense_no_files(self):
        expenseType = ExpenseType.objects.create(
            name="km-korvaus",
            active=True,
            type="T",
            requires_receipt=False,
            multiplier=0.22,
            requires_endtime=False,
            requires_start_time=False,
            persontype=1,
            account="HiihtoTili",
            unit="km",
            organisation=self.organisation)

        self.client.login(username='jacob.tester', password='top_secret',
                          person=self.person)
        response = self.client.get(
            f"/expense/new/{self.organisation.id}")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Kulukorvaus organisaatiolle'
        )
        response = self.client.post(f"/expense/new/{self.organisation.id}", data={
            "preview": '0',
            "expenseform-user": self.user.id,
            "expenseform-organisation": self.organisation.id,
            "expenseform-name": "Jacob Tester",
            "expenseform-email": "jacob.tester@test.com",
            "expenseform-phone": "044123456",
            "expenseform-address": "Esimerkkitie 123",
            "expenseform-iban": "GB33BUKB20201555555555",
            "expenseform-personno": "010101-123N",
            "expenseform-description": "description",
            "expenseform-memo": "memoteksti",
            "expenseform_EXPENSELINES-TOTAL_FORMS": 1,
            "expenseform_EXPENSELINES-INITIAL_FORMS": 0,
            "expenseform_EXPENSELINES-MIN_NUM_FORMS": 1,
            "expenseform_EXPENSELINES-MAX_NUM_FORMS": 1000,
            "expenseform_EXPENSELINES-0-basis": 100,
            "expenseform_EXPENSELINES-0-description": "Drove from Turku to helsinki",
            "expenseform_EXPENSELINES-0-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-__prefix__-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-0-sum": expenseType.multiplier*100,
            "expenseform_EXPENSELINES-0-begin_at_date": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at_time": "12.45",
            "expenseform_EXPENSELINES-0-ended_at_date": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at_time": "16.45",
            "expenseform_EXPENSELINES-0-expensetype_data": [expenseType]
        })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Kulutiedot tallennettu.'
        )

    def test_user_create_expense_with_a_file(self):
        expenseType = ExpenseType.objects.create(
            name="km-korvaus",
            active=True,
            type="O",
            requires_receipt=True,
            multiplier=1.0,
            requires_endtime=False,
            requires_start_time=False,
            persontype=1,
            account="HiihtoTili",
            unit="EUR",
            organisation=self.organisation)

        self.client.login(username='jacob.tester', password='top_secret',
                          person=self.person)
        response = self.client.get(
            f"/expense/new/{self.organisation.id}")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Kulukorvaus organisaatiolle'
        )
        receipt = SimpleUploadedFile(
            "file.jgp", b"file_content", content_type="image/jpg")
        response = self.client.post(f"/expense/new/{self.organisation.id}", data={
            "preview": '0',
            "expenseform-user": self.user.id,
            "expenseform-organisation": self.organisation.id,
            "expenseform-name": "Jacob Tester",
            "expenseform-email": "jacob.tester@test.com",
            "expenseform-phone": "044123456",
            "expenseform-address": "Esimerkkitie 123",
            "expenseform-iban": "GB33BUKB20201555555555",
            "expenseform-personno": "010101-123N",
            "expenseform-description": "description",
            "expenseform-memo": "memoteksti",
            "expenseform_EXPENSELINES-TOTAL_FORMS": 1,
            "expenseform_EXPENSELINES-INITIAL_FORMS": 0,
            "expenseform_EXPENSELINES-MIN_NUM_FORMS": 1,
            "expenseform_EXPENSELINES-MAX_NUM_FORMS": 1000,
            "expenseform_EXPENSELINES-0-basis": 100,
            "expenseform_EXPENSELINES-0-receipt": receipt,
            "expenseform_EXPENSELINES-0-description": "Drove from Turku to helsinki",
            "expenseform_EXPENSELINES-0-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-__prefix__-expensetype": expenseType.id,
            "expenseform_EXPENSELINES-0-sum": expenseType.multiplier*100,
            "expenseform_EXPENSELINES-0-begin_at_date": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at": "31.1.2022",
            "expenseform_EXPENSELINES-0-begin_at_time": "12.45",
            "expenseform_EXPENSELINES-0-ended_at_date": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at": "2.2.2022",
            "expenseform_EXPENSELINES-0-ended_at_time": "16.45",
            "expenseform_EXPENSELINES-0-expensetype_data": [expenseType]
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, 'Kulutiedot tallennettu.'
        )
