# Teaching principles for explainer videos

Use this when writing `outline.md` and `script.json`.

## The professor's contract
- **Start with a question.** People remember answers to questions they actually asked.
  Open with a problem, a paradox, or a failure case that the concept fixes.
- **Concrete before abstract.** Show a specific instance (3 tokens, a 2×2 matrix, 5 nodes)
  before the general form. Generalize only once the instance makes sense.
- **Build on what the viewer already knows.** Name the prerequisite before using it, with a
  10 to 20 second recap if needed ("Recall that a dot product measures alignment...").
- **One idea at a time.** Working memory holds about 4 chunks. If a beat introduces a new
  term, a new symbol, *and* a new visual, split it.
- **Dual coding.** Narration and visuals carry the *same* idea through different channels.
  Never put paragraphs of text on screen while the narrator says something else (the
  redundancy and split-attention effects).
- **Signal.** Use highlights, color, and motion to point at whatever the narration is
  talking about at that moment.
- **Answer "why" as well as "what".** Every formal step should be motivated: "We divide by
  root d because otherwise the dot products grow with dimension and the softmax saturates.
  Watch what happens to the distribution."
- **Confront misconceptions explicitly.** Show the wrong mental model, show where it
  breaks, then show the right one.
- **Use multiple representations.** The same idea as a picture, an equation, and a number
  example, with explicit links between them.
- **Retrieval at the end.** The recap should rebuild the idea, ideally by replaying the
  core animation with all labels in place, and can pose a "pause and predict" question.

## Analogies
- Choose an analogy whose *structure* matches the mechanism, not just its surface.
- State where the analogy breaks. A good professor says "this is where the analogy stops
  working."
- Drop the analogy once the formal picture is in place. Don't keep two models running.

## Pause-and-predict moments
In longer videos, add one or two: "Before I show you, what do you think happens when the
learning rate is too large?" Then hold for about 2 s (`pause_after`) before revealing the
answer. This turns passive watching into active thinking.

## Depth calibration
- Explain to the intended audience, not to an expert, and not to someone who knows nothing.
- If a step needs a detour longer than about 30 s, either make it its own scene or say
  explicitly that you are skipping it ("we'll take this as given; the proof is in the
  description").
- Never hand-wave the central mechanism. That's the reason the video exists.

## Script self-check
For each scene, ask:
1. What can the viewer do or explain after this scene that they couldn't before?
2. Which visual makes that possible?
3. Which word or symbol might they not know yet?
