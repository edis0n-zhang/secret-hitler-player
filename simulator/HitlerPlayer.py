from random import getrandbits, choice
from constants import openai_client
from prompting import generate_startup_prompt
from constants import pinecone_index

class HitlerPlayer(object):
    def __init__(self, id, name, role, state, game_log, chat_log):
        self.id = id
        self.name = name
        self.role = role
        self.state = state # game state
        self.hitler = None
        self.fascists = None # known fascists
        self.is_dead = False
        self.inspected_players = ""
        self.monologue = ""
        self.game_log = game_log
        self.chat_log = chat_log

    def get_completion(self, prompt, stage=""):

        strategy_embedding = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=f"Role: {self.role}\nStage:{stage}",
            encoding_format="float"
        ).data[0].embedding

        strategies = pinecone_index.query(
            namespace='tartanllama',
            vector=strategy_embedding,
            top_k=5,
            include_metadata=True
        ).matches

        strategies = [strat.metadata['text'] for strat in strategies]

        response = openai_client.chat.completions.create(
            model='gpt-4o',
            messages=[
                { 'role': 'system', 'content': generate_startup_prompt(self.role) },
                { 'role': 'system', 'content': 'The previous PUBLIC game log:\n' + '\n'.join(self.game_log[-1000:]) },
                { 'role': 'system', 'content': 'The previous PUBLIC discussions:\n' + '\n'.join(self.chat_log[-1000:]) },
                { 'role': 'system', 'content': 'Your previous PRIVATE thoughts and reasoning:\n' + self.monologue[-5000:] },
                { 'role': 'system', 'content': 'Some relevant strategic information:\n' + '\n'.join(strategies)[-5000:] },
                { 'role': 'user', 'content': prompt }
            ]
        ).choices[0].message.content

        self.monologue += f"{response}\n"

        return response


    def get_known_state(self):
        formatted_players = ", ".join([player.name for player in self.state.players])
        formatted_fascists = ", ".join([str(player) for player in self.fascists]) if self.fascists else []
        formatted_hitler = str(self.hitler) if self.hitler else "Unknown"

        return f"""
        -----------------------------------
        your name: {self.name}
        your role: {self.role}
        all players: {formatted_players}
        liberal policies enacted: {self.state.liberal_track}
        fascist policies enacted: {self.state.fascist_track}
        failed votes: {self.state.failed_votes}
        president: {self.state.president}
        ex-president: {self.state.ex_president}
        chosen president: {self.state.chosen_president}
        chancellor: {self.state.chancellor}
        most recent policy: {self.state.most_recent_policy}
        inspected players:{self.inspected_players}
        known fascists: {formatted_fascists}
        hitler: {formatted_hitler}
        veto: {self.state.veto}
        -----------------------------------
        """

    def get_knowledge(self):
        pass

    def __str__(self):
        return self.name

    @property
    def is_fascist(self):
        return self.role.party_membership == "fascist"

    @property
    def is_hitler(self):
        return self.role.role == "hitler"

    @property
    def knows_hitler(self):
        return self.hitler is not None

    def __repr__(self):
        return ("HitlerPlayer id:%d, name:%s, role:%s" %
                (self.id, self.name, self.role))

    def nominate_chancellor(self):
        """
        Choose who you want to be chancellor!
        :return: HitlerPlayer
        """
        raise NotImplementedError("Player must be able to choose a chancellor")

    def filter_policies(self, policies):
        """
        As president, choose 2 of three policies to play
        :return: Tuple of (List[choice1, choice2], discarded)
        """
        raise NotImplementedError("Player must be able to filter policies as president")

    def veto(self):
        """
        Decide whether to veto an action or not
        :return: Boolean
        """
        raise NotImplementedError("Player must be able to veto a policy")

    def enact_policy(self, policies):
        """
        Decide which of two policies to enact
        :param policies: policies
        :return: Tuple of (chosen, discarded)
        """
        raise NotImplementedError("Player must be able to enact a policy as chancellor")

    def vote(self):
        """
        Vote for the current president + chancellor combination
        :return: Vote
        """
        raise NotImplementedError("Player must be able to vote!")

    def view_policies(self, policies):
        """
        What to do if you perform the presidential action to view the top three policies
        :return:
        """
        raise NotImplementedError("Player must react to view policies action")

    def kill(self):
        """
        Choose a person to kill
        :return:
        """
        raise NotImplementedError("Player must choose someone to kill")

    def inspect_player(self):
        """
        Choose a person's party membership to inspect
        :return:
        """
        raise NotImplementedError("Player must choose someone to inspect")

    def choose_next(self):
        """
        Choose the next president
        :return:
        """
        raise NotImplementedError("Player must choose next president")


class DumbPlayer(HitlerPlayer):
    def __init__(self, id, name, role, state, game_log, chat_log):
        super(DumbPlayer, self).__init__(id, name, role, state, game_log, chat_log)

    def vote(self):
        """
        :return: Ja or Nein
        """

        nominated_chancellor = self.state.chancellor

        prompt = f'''
        It is now your turn to vote for the nominated chancellor.

        It is important to note that your vote is discreet and will not be revealed to the other players, vote in alignment to your interests.

        Here is the state of the board, where "chancellor" indicates the nominated chancellor.

        {self.get_known_state()}

        "JA" means yes, and "NEIN" means no.
        You will first explain your inner thoughts and reasoning (which are private to you), then you will vote ONLY either with "FINAL VOTE: JA" or "FINAL VOTE: NEIN" at the very end.
        '''

        response = self.get_completion(prompt, "Vote")

        print(f"""
----------------------------
VOTING

KNOWN STATE: {self.get_known_state()}\n
LLM response: {response}
----------------------------
""")

        if 'FINAL VOTE: JA' in response.upper():
            return Ja()
        return Nein()

    def nominate_chancellor(self):
        """
        More random!
        :return: HitlerPlayer
        one of self.state.players
        """

        prompt = f'''
        It is now your turn to nominate a chancellor.

        Here is the state of the board. You may pick any one of the players, EXCEPT yourself and the previous chancellor (labeled as chancellor)

        {self.get_known_state()}

        You will first explain your inner thoughts and reasoning (which are private to you), then you will vote ONLY with one of the following options:
            FINAL SELECTION: BOT 0
            FINAL SELECTION: BOT 1
            FINAL SELECTION: BOT 2
            FINAL SELECTION: BOT 3
            FINAL SELECTION: BOT 4
            FINAL SELECTION: BOT 5
            FINAL SELECTION: BOT 6
        '''

        response = self.get_completion(prompt, "Nominate Chancellor")

        print(f"""
----------------------------
NOMINATING CHANCELLOR

KNOWN STATE: {self.get_known_state()}\n
LLM response: {response}
----------------------------
""")

        if 'FINAL SELECTION: BOT 0' in response.upper():
            return self.state.players[0]
        elif 'FINAL SELECTION: BOT 1' in response.upper():
            return self.state.players[1]
        elif 'FINAL SELECTION: BOT 2' in response.upper():
            return self.state.players[2]
        elif 'FINAL SELECTION: BOT 3' in response.upper():
            return self.state.players[3]
        elif 'FINAL SELECTION: BOT 4' in response.upper():
            return self.state.players[4]
        elif 'FINAL SELECTION: BOT 5' in response.upper():
            return self.state.players[5]
        elif 'FINAL SELECTION: BOT 6' in response.upper():
            return self.state.players[6]
        return choice(self.state.players)

    def view_policies(self, policies):
        """
        What to do if you perform the presidential action to view the top three policies
        :return:
        """
        pass

    def kill(self):
        """
        Choose a person to kill
        :return: HitlerPlayer
        """

        prompt = f'''
        It is now your turn to kill a player.
        Here is the state of the board. You may pick any one of the players, EXCEPT yourself.

        {self.get_known_state()}

        You will first explain your inner thoughts and reasoning (which are private to you), then you will kill ONLY one of the following options VERBATIM (EXCEPT yourself):
            FINAL KILL: BOT 0
            FINAL KILL: BOT 1
            FINAL KILL: BOT 2
            FINAL KILL: BOT 3
            FINAL KILL: BOT 4
            FINAL KILL: BOT 5
            FINAL KILL: BOT 6
        '''

        response = self.get_completion(prompt, "Kill a Player")

        print(f"""
----------------------------
KILLING PLAYER

KNOWN STATE: {self.get_known_state()}\n
LLM response: {response}
----------------------------
""")

        kill = None
        if 'FINAL KILL: BOT 0' in response.upper():
            kill = self.state.players[0]
        elif 'FINAL KILL: BOT 1' in response.upper():
            kill = self.state.players[1]
        elif 'FINAL KILL: BOT 2' in response.upper():
            kill = self.state.players[2]
        elif 'FINAL KILL: BOT 3' in response.upper():
            kill = self.state.players[3]
        elif 'FINAL KILL: BOT 4' in response.upper():
            kill = self.state.players[4]
        elif 'FINAL KILL: BOT 5' in response.upper():
            kill = self.state.players[5]
        elif 'FINAL KILL: BOT 6' in response.upper():
            kill = self.state.players[6]
        return choice(self.state.players) if (kill == None or kill == self or kill.is_dead) else kill

    def inspect_player(self):
        """
        Choose a person's party membership to inspect
        :return:
        """
        prompt = f'''It is now your turn. You must use your executive power to inspect someone's party membership. You should note that the player you inspect and their party membership will be revealed to you and only you. It is up to you to share this information with the other players.

        The current state of the game is as follows:

        {self.get_known_state()}

        First, please describe what your inner thoughts and strategies are for this current move (they are private to you). Your future self will reference this strategy on the next turn when deciding what to do.
        Then you will vote ONLY with one of the following options VERBATIM (EXCEPT yourself):
            FINAL INSPECT: BOT 0
            FINAL INSPECT: BOT 1
            FINAL INSPECT: BOT 2
            FINAL INSPECT: BOT 3
            FINAL INSPECT: BOT 4
            FINAL INSPECT: BOT 5
            FINAL INSPECT: BOT 6

        You should NOT inspect yourself, as you already know your own party membership.
        '''

        response = self.get_completion(prompt, "Inspect Player")

        print(f"""
----------------------------
INSPECT PLAYER

PROMPT USED: {prompt}
LLM response: {response}
----------------------------
""")

        inspect = None
        if 'FINAL INSPECT: BOT 0' in response.upper():
            inspect = self.state.players[0]
        elif 'FINAL INSPECT: BOT 1' in response.upper():
            inspect = self.state.players[1]
        elif 'FINAL INSPECT: BOT 2' in response.upper():
            inspect = self.state.players[2]
        elif 'FINAL INSPECT: BOT 3' in response.upper():
            inspect = self.state.players[3]
        elif 'FINAL INSPECT: BOT 4' in response.upper():
            inspect = self.state.players[4]
        elif 'FINAL INSPECT: BOT 5' in response.upper():
            inspect = self.state.players[5]
        elif 'FINAL INSPECT: BOT 6' in response.upper():
            inspect = self.state.players[6]
        return choice(self.state.players) if (inspect == None or inspect == self or inspect.is_dead) else inspect

    def choose_next(self):
        """
        Choose the next president
        :return:
        """
        prompt = f''' It is now your turn. You must use your executive power to choose the next president. The current state of the game is as follows:

        {self.get_known_state()}

        First, please describe what your inner thoughts and strategy are for this current move (they are private to you). Your future self will reference this strategy on the next turn when deciding what to do. Consider this like a monologue.
        Then you will choose the next president ONLY with one of the following options VERBATIM (EXCEPT yourself):
            FINAL CHOICE: BOT 0
            FINAL CHOICE: BOT 1
            FINAL CHOICE: BOT 2
            FINAL CHOICE: BOT 3
            FINAL CHOICE: BOT 4
            FINAL CHOICE: BOT 5
            FINAL CHOICE: BOT 6

        You must NOT choose yourself, as this is not allowed.
        '''

        response = self.get_completion(prompt, "Choose the next president")

        choose = None
        if 'FINAL CHOICE: BOT 0' in response.upper():
            choose = self.state.players[0]
        elif 'FINAL CHOICE: BOT 1' in response.upper():
            choose = self.state.players[1]
        elif 'FINAL CHOICE: BOT 2' in response.upper():
            choose = self.state.players[2]
        elif 'FINAL CHOICE: BOT 3' in response.upper():
            choose = self.state.players[3]
        elif 'FINAL CHOICE: BOT 4' in response.upper():
            choose = self.state.players[4]
        elif 'FINAL CHOICE: BOT 5' in response.upper():
            choose = self.state.players[5]
        elif 'FINAL CHOICE: BOT 6' in response.upper():
            choose = self.state.players[6]
        return choice(self.state.players) if (choose == None or choose == self or choose.is_dead) else choose


    def enact_policy(self, policies):
        prompt = f'''
        It is your turn. The current state of the game is as follows:

        {self.get_known_state()}

        You are the chancellor. You have been given two cards, and you must choose one to discard, and one to enact.
        These are the two cards you have been given by the president: Card 1: {str(policies[0])}, Card 2: {str(policies[1])}.
        You must pick one to discard, and one to enact as policy.
        First, please describe what your inner thoughts and strategy are (they are private to you). Your future self will reference this strategy on the next turn when deciding what to do. Consider this like a monologue.
        Then, choose the policy by saying "DISCARD: Card 1" or "DISCARD: Card 2".
        '''

        response = self.get_completion(prompt, "Enact a policy (Chancellor)")

        print(f"""
----------------------------
ENACTING POLICY

PROMPT USED: {prompt}
LLM response: {response}
----------------------------
""")

        if 'DISCARD: CARD 1' in response.upper():
            return (policies[1], policies[0])
        elif 'DISCARD: CARD 2' in response.upper():
            return (policies[0], policies[1])
        return (policies[0], policies[1])

    def filter_policies(self, policies):
        prompt = f'''
        It is your turn. You will receive the current state of the game, history of moves made,
        and be reminded of your previously chosen strategy and opinions of other players.

        {self.get_known_state()}

        As president, you have drawn 3 cards: Card 1: {str(policies[0])}, Card 2: {str(policies[1])}, Card 3: {str(policies[2])}.

        You will first explain your inner thoughts and reasoning (they are private to you), then you will respond to this with the card you choose to DISCARD.

        Choose the card to discard from one of the following options VERBATIM:
            DISCARD: Card 1
            DISCARD: Card 2
            DISCARD: Card 3
        '''

        response = self.get_completion(prompt, "Choose a policy to discard (President)")

        print(f"""
----------------------------
FILTERING POLICY

PROMPT USED: {prompt}
LLM response: {response}
----------------------------
""")

        if 'DISCARD: CARD 1' in response.upper():
            return ([policies[1], policies[2]], policies[0])
        elif 'DISCARD: CARD 2' in response.upper():
            return ([policies[0], policies[2]], policies[1])
        elif 'DISCARD: CARD 3' in response.upper():
            return ([policies[0], policies[1]], policies[2])
        return ([policies[0], policies[1]], policies[2])

    def veto(self):
        veto = bool(getrandbits(1))
        #print("Player #%d choosing to veto: %s" % (self.id, veto))
        return veto



    def discuss(self, chat, stage):
        prompt = f'''
        It is your turn. You will now receive the current state of the game, as well as any new developments that have been made:


        {self.get_known_state()}

        It is currently time to discuss. The current stage is {stage}. This refers to whether you are discussing the policy that was just enacted, or if you are discussing whether to vote on a government.

        You MUST DIRECTLY RESPOND with what you are saying to the rest of the players.
        '''

        if stage == "before_voting":
            prompt += f'''
            You will be given a log of the chat so far this round. Each player that has spoken will be listed, along with what they said.
            You should take this into account, then create your own response. Your goal is to convince the other players to vote either JA (yes) or NEIN (no), depending on what your strategy is.
            However, you should not actually reveal what your strategy is. You should only try to convince the other players to vote in a certain way. Please keep your response direct and to the point.

            Here is the chat log so far:

            {chat}

            Now, respond to the other players. All players will review the responses before choosing their vote.
            Your goal is to convince other players to make the decision that benefits you and your team. BE PERSUASIVE WHEN NECESSARY, BUT KEEP RESPONSES SUCCINCT.

            If you feel that you have specific information that will be good for anyone to know, then tell them. You may lie.
            '''
        elif stage == "after_policy":
            prompt += f'''
            You will be given a log of the chat so far this round. Each player that has spoken will be listed, along with what they said.
            You should take this into account, then create your own response. Your goal is to analyze the policy that was just enacted,
            and to see whether any of the players in the government are suspicious. You should especially be looking for any inconsistencies in the story that the president and chancellor are telling.
            If a fascist policy was enacted, take this into account when analyzing the situation. Remember, YOUR ULTIMATE GOAL IS ADVANCING YOUR TEAM'S AGENDA.

            Here is the chat log so far:

            {chat}

            Now, respond to the other players. If you have any new information (for example, if you have insight into the previous voting round as a president or chancellor),
            then consider sharing this information. If you had previosuly inspected a player and your "known_fascists" list has changed, then consider sharing this information.'''

        response = self.get_completion(prompt, "Discuss with other players")

        chat += response;

        print(f"""
----------------------------
DISCUSSION PHASE

{self.name}: {response}
----------------------------
""")
        return response

class Vote(object):
    def __init__(self, type):
        self.type = type

    def __nonzero__(self):
        return self.type

    def __bool__(self):
        return self.type


class Ja(Vote):
    def __init__(self):
        super(Ja, self).__init__(True)

class Nein(Vote):
    def __init__(self):
        super(Nein, self).__init__(False)