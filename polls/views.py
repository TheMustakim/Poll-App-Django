from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from .models import Choice, Question


def home(request):
    return render(request, 'polls/home.html')


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voted_questions = self.request.session.get('voted_questions', {})
        context['voted_choice_id'] = voted_questions.get(str(self.object.id))
        return context


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voted_questions = self.request.session.get('voted_questions', {})
        voted_choice_id = voted_questions.get(str(self.object.id))

        voted_choice_text = None
        if voted_choice_id:
            try:
                voted_choice = self.object.choice_set.get(pk=voted_choice_id)
                voted_choice_text = voted_choice.choice_text
            except Choice.DoesNotExist:
                voted_choice_text = None

        context['voted_choice_text'] = voted_choice_text
        return context


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    voted_questions = request.session.get('voted_questions', {})

    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(request, "polls/detail.html", {
            "question": question,
            "error_message": "You didn't select a choice.",
            "voted_choice_id": voted_questions.get(str(question.id))
        })

    # Decrement previous choice if exists
    previous_choice_id = voted_questions.get(str(question_id))
    if previous_choice_id:
        prev_choice = question.choice_set.get(pk=previous_choice_id)
        if prev_choice.votes > 0:
            prev_choice.votes -= 1
            prev_choice.save()

    # Increment selected choice
    selected_choice.votes = F("votes") + 1
    selected_choice.save()

    # Save current vote in session
    voted_questions[str(question_id)] = selected_choice.id
    request.session['voted_questions'] = voted_questions

    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
