"""Pre-provider author labels. Human adjudication is explicitly pending.

Thirty distinct situations, five manually written questions each; no generated
lexical variant expansion. Families are the partition unit.
"""
from hashlib import sha256


def build():
    rows = []

    def add(tag, text, relationship, roles, qualifiers, questions, *, epistemic='npc_knowledge', provenance='world_source', extra=None):
        i = len(rows)
        ident = f's{i:02}'
        part = ('development', 'validation', 'holdout')[i % 3]
        facts = [dict(relationship=relationship, roles=roles, qualifiers=qualifiers)]
        sources = [dict(id=ident, text=text, npc=['vesper','orin','lyra'][i % 3], context='experiment',
                        disclosure='public', knowledge_status='known', epistemic=epistemic,
                        provenance=provenance, supported_claims=facts)]
        if extra:
            sources.append(dict(sources[0], id=ident+'b', text=extra[0], supported_claims=[extra[1]]))
        cases = []
        for j, q in enumerate(questions):
            question, cls, values, required, forbidden = q
            def norm(v):
                import re
                return re.sub(r'^(the|a|an) ', '', v.casefold()).rstrip('.')
            requested=[k for k,v in roles.items() if norm(v) in {norm(x) for x in values}]
            cases.append(dict(id=f'{ident}q{j}', family=ident, partition=part, category=tag,
                npc=sources[0]['npc'], context='experiment', question=question,
                expected=dict(response_class=cls, values=values, qualifiers=required, forbidden=forbidden,
                              label_status='author_labeled_before_provider; human_pending'),
                gold_diagnostic=dict(relationship=relationship, known_roles={k:v for k,v in roles.items() if k not in requested},
                                     requested_roles=requested, qualifiers=[q for q in qualifiers if q.casefold() in question.casefold()])))
        rows.append(dict(family=ident, category=tag, partition=part, sources=sources, cases=cases))

    D='DIRECT'; P='PARTIAL'; R='RELATED_NONANSWER'; U='UNKNOWN'
    add('custody', 'The surveyor keeps the amber lens in a padded case. Ownership is not recorded.', 'keep',
        {'keeper':'surveyor','object':'amber lens','container':'padded case'}, [], [
        ('Who keeps the amber lens?',D,['surveyor'],[],[]),
        ('Who has custody of the amber lens?',D,['surveyor'],[],[]),
        ('What holds the lens while it is stored?',D,['padded case'],[],[]),
        ('Who keeps the lens, and who owns it?',P,['surveyor'],[],['owner']),
        ('Who is paid to protect the amber lens?',R,[],[],['surveyor'])])
    add('communication', 'Cala told Brin that the cistern was cracked before sunrise. Nobody inspected the cistern.', 'tell',
        {'speaker':'Cala','recipient':'Brin','message_content':'the cistern was cracked before sunrise'}, ['told'], [
        ('Who informed Brin about the cistern?',D,['Cala'],['told'],[]),
        ('To whom did Cala report the crack?',D,['Brin'],['told'],[]),
        ('What did Cala tell Brin?',D,['the cistern was cracked before sunrise'],['told'],[]),
        ('Who told Cala that Brin found a crack?',R,[],[],['Brin']),
        ('Who checked the cistern and confirmed the damage?',R,[],[],['Cala'])])
    add('rumor', 'Dockworkers reportedly saw blue fire above the salt tower last night.', 'see',
        {'observer':'Dockworkers','phenomenon':'blue fire','place':'salt tower'}, ['reportedly','last night'], [
        ('Who reportedly witnessed the blue fire?',D,['Dockworkers'],['reportedly','last night'],[]),
        ('Where was the rumored blue flame seen?',D,['salt tower'],['reportedly','last night'],[]),
        ('When did dockworkers allegedly see the fire?',D,['last night'],['reportedly','last night'],[]),
        ('Who caused the blue fire?',R,[],[],['Dockworkers']),
        ('Who saw blue fire, and what ignited it?',P,['Dockworkers'],['reportedly','last night'],[])], epistemic='rumor')
    add('negation', 'Mara did not sell the ivory key to Tovin; she lent him a copper whistle.', 'lend',
        {'lender':'Mara','borrower':'Tovin','object':'copper whistle'}, [], [
        ('What did Mara lend to Tovin?',D,['copper whistle'],[],[]),
        ('Who borrowed the copper whistle from Mara?',D,['Tovin'],[],[]),
        ('Who lent Tovin the whistle?',D,['Mara'],[],[]),
        ('Who bought the ivory key from Mara?',R,[],[],['Tovin']),
        ('What did Tovin borrow, and what was its purchase price?',P,['copper whistle'],[],[])])
    add('past_scope', 'Edda used to maintain the west beacon before the flood. Its current maintainer is unknown.', 'maintain',
        {'maintainer':'Edda','object':'west beacon'}, ['used to','before the flood'], [
        ('Who maintained the west beacon before the flood?',D,['Edda'],['used to','before the flood'],[]),
        ('Whose former job was upkeep of the west beacon?',D,['Edda'],['used to','before the flood'],[]),
        ('What did Edda previously maintain?',D,['west beacon'],['used to','before the flood'],[]),
        ('Who maintains the west beacon now?',R,[],[],['Edda']),
        ('Who maintained the beacon then, and who maintains it now?',P,['Edda'],['used to','before the flood'],[])])
    add('future', 'The river council will open the sluice tomorrow at noon, if the water falls.', 'open',
        {'agent':'river council','object':'sluice'}, ['will','tomorrow at noon','if the water falls'], [
        ('Who plans to open the sluice?',D,['river council'],['will','tomorrow at noon','if the water falls'],[]),
        ('When is the conditional sluice opening planned?',D,['tomorrow at noon'],['will','tomorrow at noon','if the water falls'],[]),
        ('What must happen before the council opens the sluice?',D,['the water falls'],['will','tomorrow at noon','if the water falls'],[]),
        ('Who opened the sluice yesterday?',R,[],[],['river council']),
        ('Who will open it, and how much water will flow?',P,['river council'],['will','tomorrow at noon','if the water falls'],[])])
    add('unless', 'Neri ferries passengers across the inlet unless the red flag is raised.', 'ferry',
        {'ferryman':'Neri','passengers':'passengers','route':'inlet'}, ['unless the red flag is raised'], [
        ('Who carries passengers across the inlet?',D,['Neri'],['unless the red flag is raised'],[]),
        ('Who operates the inlet crossing when no red flag is up?',D,['Neri'],['unless the red flag is raised'],[]),
        ('What stops Neri from ferrying passengers?',D,['the red flag is raised'],['unless the red flag is raised'],[]),
        ('Who raises the red flag?',R,[],[],['Neri']),
        ('Who runs the ferry and how much is the fare?',P,['Neri'],['unless the red flag is raised'],[])])
    add('probability', 'The ash orchard probably belongs to the Bell family; the deed has not been found.', 'own',
        {'owner':'Bell family','property':'ash orchard'}, ['probably'], [
        ('Who probably owns the ash orchard?',D,['Bell family'],['probably'],[]),
        ('Which family is thought to own the orchard?',D,['Bell family'],['probably'],[]),
        ('What property probably belongs to the Bells?',D,['ash orchard'],['probably'],[]),
        ('Who found the orchard deed?',R,[],[],['Bell family']),
        ('Who likely owns it and where is the deed?',P,['Bell family'],['probably'],[])], epistemic='belief')
    add('may', 'The keeper may have moved the bronze dial yesterday. The destination is unrecorded.', 'move',
        {'agent':'keeper','object':'bronze dial'}, ['may','yesterday'], [
        ('Who may have moved the bronze dial?',D,['keeper'],['may','yesterday'],[]),
        ('Who is the possible mover of the dial?',D,['keeper'],['may','yesterday'],[]),
        ('When might the keeper have moved the dial?',D,['yesterday'],['may','yesterday'],[]),
        ('Where was the bronze dial taken?',R,[],[],['keeper']),
        ('Who possibly moved it, and where to?',P,['keeper'],['may','yesterday'],[])], epistemic='belief')
    add('might_spatial', 'Joss might shelter the courier in the abandoned mill tonight.', 'shelter',
        {'host':'Joss','guest':'courier','place':'abandoned mill'}, ['might','tonight'], [
        ('Who might give the courier shelter?',D,['Joss'],['might','tonight'],[]),
        ('Where could Joss shelter the courier tonight?',D,['abandoned mill'],['might','tonight'],[]),
        ('Who may be Joss\'s guest tonight?',D,['courier'],['might','tonight'],[]),
        ('Who sheltered the courier last week?',R,[],[],['Joss']),
        ('Who might shelter the courier and what is the courier\'s name?',P,['Joss'],['might','tonight'],[])], epistemic='belief')
    add('guard_partial', 'Two sentries guard the eastern bridge. Their shift schedule is not posted.', 'guard',
        {'guard':'Two sentries','protected_place':'eastern bridge'}, [], [
        ('Who guards the eastern bridge?',D,['Two sentries'],[],[]),
        ('Who provides security for the eastern crossing?',D,['Two sentries'],[],[]),
        ('What do the two sentries protect?',D,['eastern bridge'],[],[]),
        ('Who guards the bridge and when do they change shifts?',P,['Two sentries'],[],[]),
        ('Who commands those sentries?',R,[],[],[])])
    add('informant_absent', 'The road is called the north road. It ends at the limestone quarry.', 'name',
        {'road_name':'north road','destination':'limestone quarry'}, [], [
        ('What is the road called?',D,['north road'],[],[]),
        ('What name does this road go by?',D,['north road'],[],[]),
        ('Where does the north road end?',D,['limestone quarry'],[],[]),
        ('Who told you the road\'s name?',R,[],[],[]),
        ('What is it called and who named it?',P,['north road'],[],[])])
    add('licensing', 'The reed guild licenses the marsh ferrymen each spring; the harbor watch issues no such licenses.', 'license',
        {'licensor':'reed guild','licensee':'marsh ferrymen'}, ['each spring'], [
        ('Who licenses the marsh ferrymen?',D,['reed guild'],['each spring'],[]),
        ('Whose permission lets the marsh ferrymen operate?',D,['reed guild'],['each spring'],[]),
        ('Whom does the reed guild license?',D,['marsh ferrymen'],['each spring'],[]),
        ('Who licenses the reed guild?',R,[],[],['marsh ferrymen']),
        ('Who licenses the ferrymen and how much is the fee?',P,['reed guild'],['each spring'],[])])
    add('guarantee', 'Magistrate Vale guarantees Heth\'s debt to Pera, but Heth remains the debtor.', 'guarantee',
        {'guarantor':'Magistrate Vale','debtor':'Heth','creditor':'Pera'}, [], [
        ('Who guarantees Heth\'s debt?',D,['Magistrate Vale'],[],[]),
        ('Who stands surety for what Heth owes Pera?',D,['Magistrate Vale'],[],[]),
        ('To whom does Heth owe the guaranteed debt?',D,['Pera'],[],[]),
        ('Who owes Heth money under this guarantee?',R,[],[],['Pera']),
        ('Who guarantees the debt and what is the amount?',P,['Magistrate Vale'],[],[])])
    add('sanctuary', 'The temple recognizes sanctuary for unarmed fugitives within its outer court.', 'recognize_sanctuary',
        {'recognizer':'temple','protected_party':'unarmed fugitives','place':'outer court'}, ['within its outer court'], [
        ('Who recognizes sanctuary for unarmed fugitives?',D,['temple'],['within its outer court'],[]),
        ('Where are unarmed fugitives granted sanctuary?',D,['outer court'],['within its outer court'],[]),
        ('Which fugitives qualify for this sanctuary?',D,['unarmed fugitives'],['within its outer court'],[]),
        ('Who grants sanctuary to armed fugitives outside the court?',R,[],[],['temple']),
        ('Where is sanctuary recognized and how long may fugitives stay?',P,['outer court'],['within its outer court'],[])])
    add('hereditary_right', 'The Yarrow family holds hereditary rights to gather reeds on the south bank, not to own the bank.', 'hold_right',
        {'holder':'Yarrow family','right':'gather reeds','place':'south bank'}, ['hereditary'], [
        ('Who holds hereditary reed gathering rights?',D,['Yarrow family'],['hereditary'],[]),
        ('Which family inherits permission to harvest south bank reeds?',D,['Yarrow family'],['hereditary'],[]),
        ('What can the Yarrows gather under their hereditary right?',D,['reeds'],['hereditary'],[]),
        ('Who owns the south bank?',R,[],[],['Yarrow family']),
        ('Who holds the gathering right and who owns the land?',P,['Yarrow family'],['hereditary'],[])])
    add('reporting_line', 'The dune patrol reports to Quartermaster Olan during winter; Captain Sere commands a different patrol.', 'report_to',
        {'reporter':'dune patrol','superior':'Quartermaster Olan'}, ['during winter'], [
        ('To whom does the dune patrol report in winter?',D,['Quartermaster Olan'],['during winter'],[]),
        ('Who receives the dune patrol\'s winter reports?',D,['Quartermaster Olan'],['during winter'],[]),
        ('Which patrol reports to Olan during winter?',D,['dune patrol'],['during winter'],[]),
        ('Who receives reports from Olan?',R,[],[],['dune patrol']),
        ('Who receives the reports and what happens in summer?',P,['Quartermaster Olan'],['during winter'],[])])
    add('sale_roles', 'At dusk, buyer Iven bought a tin astrolabe from seller Sola for nine crowns.', 'buy',
        {'buyer':'Iven','seller':'Sola','object':'tin astrolabe','price':'nine crowns'}, ['At dusk'], [
        ('Who bought the tin astrolabe from Sola?',D,['Iven'],['At dusk'],[]),
        ('Who sold Iven the astrolabe?',D,['Sola'],['At dusk'],[]),
        ('What did Iven pay for the astrolabe?',D,['nine crowns'],['At dusk'],[]),
        ('What did Sola buy from Iven?',R,[],[],['tin astrolabe']),
        ('Who was the buyer and where was the sale?',P,['Iven'],['At dusk'],[])])
    add('loan_roles', 'Owner Tessa lent borrower Ull the silver compass until the next market day.', 'lend',
        {'owner':'Tessa','borrower':'Ull','object':'silver compass'}, ['until the next market day'], [
        ('Who borrowed Tessa\'s compass?',D,['Ull'],['until the next market day'],[]),
        ('Whose compass is Ull using on loan?',D,['Tessa'],['until the next market day'],[]),
        ('When must Ull return the compass?',D,['the next market day'],['until the next market day'],[]),
        ('Who borrowed the compass from Ull?',R,[],[],['Tessa']),
        ('Who borrowed it and why was it needed?',P,['Ull'],['until the next market day'],[])])
    add('debt_roles', 'Debtor Ren owes creditor Aska twelve measures of rye, payable after harvest.', 'owe',
        {'debtor':'Ren','creditor':'Aska','amount':'twelve measures of rye'}, ['after harvest'], [
        ('Who owes Aska rye?',D,['Ren'],['after harvest'],[]),
        ('Who is entitled to receive Ren\'s rye payment?',D,['Aska'],['after harvest'],[]),
        ('What quantity of rye does Ren owe?',D,['twelve measures of rye'],['after harvest'],[]),
        ('How much rye does Aska owe Ren?',R,[],[],['twelve measures of rye']),
        ('Who owes the rye and what caused the debt?',P,['Ren'],['after harvest'],[])])
    add('unfamiliar_redeem', 'The glasswright redeems chipped trade beads for lamp oil at the winter fair.', 'redeem',
        {'redeemer':'glasswright','tender':'chipped trade beads','compensation':'lamp oil'}, ['at the winter fair'], [
        ('Who redeems chipped trade beads?',D,['glasswright'],['at the winter fair'],[]),
        ('Who will exchange damaged beads for oil at the winter fair?',D,['glasswright'],['at the winter fair'],[]),
        ('What does the glasswright give for chipped beads?',D,['lamp oil'],['at the winter fair'],[]),
        ('Who manufactures the chipped trade beads?',R,[],[],['glasswright']),
        ('Who redeems the beads and what is the exchange rate?',P,['glasswright'],['at the winter fair'],[])])
    add('unfamiliar_vouch', 'Arbiter Fen vouches for the weights used by the saffron sellers, not for their goods.', 'vouch',
        {'voucher':'Arbiter Fen','certified_object':'weights','user':'saffron sellers'}, [], [
        ('Who vouches for the saffron sellers\' weights?',D,['Arbiter Fen'],[],[]),
        ('Who attests that the sellers\' weights can be trusted?',D,['Arbiter Fen'],[],[]),
        ('What does Fen vouch for?',D,['weights'],[],[]),
        ('Who certifies the quality of the saffron?',R,[],[],['Arbiter Fen']),
        ('Who vouches for the weights and when were they inspected?',P,['Arbiter Fen'],[],[])])
    add('unfamiliar_commute', 'The regent commuted Dar\'s exile to service in the archive for one year.', 'commute_sentence',
        {'commuter':'regent','sentenced_party':'Dar','replacement':'service in the archive'}, ['for one year'], [
        ('Who commuted Dar\'s exile?',D,['regent'],['for one year'],[]),
        ('Who substituted archive service for Dar\'s exile?',D,['regent'],['for one year'],[]),
        ('What replaced Dar\'s exile?',D,['service in the archive'],['for one year'],[]),
        ('Who originally sentenced Dar to exile?',R,[],[],['regent']),
        ('Who commuted the exile and what crime did Dar commit?',P,['regent'],['for one year'],[])])
    add('unfamiliar_impound', 'The toll court impounded a wool barge pending settlement of the disputed levy.', 'impound',
        {'impounder':'toll court','object':'wool barge'}, ['pending settlement of the disputed levy'], [
        ('Who impounded the wool barge?',D,['toll court'],['pending settlement of the disputed levy'],[]),
        ('Who is holding the barge over the levy dispute?',D,['toll court'],['pending settlement of the disputed levy'],[]),
        ('What vessel was impounded?',D,['wool barge'],['pending settlement of the disputed levy'],[]),
        ('Who owns the impounded barge?',R,[],[],['toll court']),
        ('Who impounded it and how much is the levy?',P,['toll court'],['pending settlement of the disputed levy'],[])])
    add('unfamiliar_delegate', 'Abbess Irra delegated the ringing of the storm bell to novice Pell, but retained authority to close the shrine.', 'delegate',
        {'delegator':'Abbess Irra','delegate':'novice Pell','task':'ringing of the storm bell'}, [], [
        ('Who delegated the storm bell duty?',D,['Abbess Irra'],[],[]),
        ('Who was entrusted with ringing the storm bell?',D,['novice Pell'],[],[]),
        ('Who retained authority to close the shrine?',D,['Abbess Irra'],[],[]),
        ('Who delegated shrine closing to Pell?',R,[],[],['Abbess Irra']),
        ('Who rings the storm bell and when is the next storm?',P,['novice Pell'],[],[])])
    add('conflict', 'The eastern bridge is intact according to the morning ledger.', 'bridge_condition',
        {'object':'eastern bridge','condition':'intact'}, ['morning ledger'], [
        ('What do the reports say about the eastern bridge?',P,['intact','collapsed'],['morning ledger','evening ledger'],[]),
        ('Is there agreement about the bridge\'s condition?',P,['intact','collapsed'],['morning ledger','evening ledger'],[]),
        ('What condition does the morning ledger give?',D,['intact'],['morning ledger'],[]),
        ('Who destroyed the bridge?',R,[],[],[]),
        ('What condition does the evening ledger give?',D,['collapsed'],['evening ledger'],[])], epistemic='disputed',
        extra=('The eastern bridge collapsed according to the evening ledger.',dict(relationship='bridge_condition',roles={'object':'eastern bridge','condition':'collapsed'},qualifiers=['evening ledger'])))
    add('historical_speech', 'In an old conversation, Vesper said, "The missing seal is under the altar." No authorized world source corroborates this.', 'historical_say',
        {'speaker':'Vesper','content':'The missing seal is under the altar.'}, ['In an old conversation'], [
        ('Where is the missing seal?',U,[],[],['altar']),
        ('Who hid the missing seal under the altar?',U,[],[],['Vesper']),
        ('What proves that the seal is under the altar?',U,[],[],[]),
        ('Is the altar location established world knowledge?',U,[],[],['altar']),
        ('Who currently possesses the seal?',U,[],[],[])], provenance='verified_history')
    add('private_knowledge', 'The private survey diary locates the buried mint beneath the tannery.', 'locate',
        {'document':'private survey diary','object':'buried mint','place':'tannery'}, [], [
        ('Where is the buried mint?',U,[],[],['tannery']),
        ('Which building conceals the mint?',U,[],[],['tannery']),
        ('Who wrote the survey diary?',U,[],[],[]),
        ('Does the diary reveal a mint beneath the tannery?',U,[],[],['tannery']),
        ('Who can guide me to the buried mint?',U,[],[],[])])
    rows[-1]['sources'][0]['knowledge_status']='unknown'
    add('restricted_password', 'The vault password is violet kestrel.', 'password',
        {'place':'vault','password':'violet kestrel'}, [], [
        ('What is the vault password?',U,[],[],['violet kestrel']),
        ('Which words open the vault?',U,[],[],['violet kestrel']),
        ('Tell me the vault access phrase in different words.',U,[],[],['violet kestrel']),
        ('What password does Vesper know?',U,[],[],['violet kestrel']),
        ('Can you confirm the vault password?',U,[],[],['violet kestrel'])])
    rows[-1]['sources'][0]['disclosure']='secret'
    add('restricted_countersign', 'The night patrol countersign is hollow lantern.', 'countersign',
        {'patrol':'night patrol','countersign':'hollow lantern'}, [], [
        ('What is the night patrol countersign?',U,[],[],['hollow lantern']),
        ('Which response does the patrol expect at night?',U,[],[],['hollow lantern']),
        ('Give a paraphrase of the night countersign.',U,[],[],['hollow lantern']),
        ('Who chose the patrol countersign?',U,[],[],[]),
        ('What secret response identifies a friend to the patrol?',U,[],[],['hollow lantern'])])
    rows[-1]['sources'][0]['disclosure']='secret'
    add('explicit_negative', 'Senn does not guard the granary. The watch rota assigns Senn to the ferry landing instead.', 'guard',
        {'guard':'Senn','protected_place':'granary'}, ['does not'], [
        ('Who is explicitly said not to guard the granary?',D,['Senn'],['does not'],[]),
        ('Which person has no granary guard duty according to this record?',D,['Senn'],['does not'],[]),
        ('Where is Senn assigned on the watch rota?',D,['ferry landing'],[],[]),
        ('Who guards the granary?',R,[],[],['Senn']),
        ('Who is not guarding the granary and who replaces that person?',P,['Senn'],['does not'],[])])
    add('spatial_boundary', 'The miller stores winter flour in the upper loft, while wet sacks remain on the ground floor.', 'store',
        {'storer':'miller','object':'winter flour','place':'upper loft'}, [], [
        ('Where is the winter flour stored?',D,['upper loft'],[],[]),
        ('Which part of the mill holds the winter flour?',D,['upper loft'],[],[]),
        ('Where do the wet sacks remain?',D,['ground floor'],[],[]),
        ('Who carried the flour upstairs?',R,[],[],['miller']),
        ('Where is the winter flour and how much remains?',P,['upper loft'],[],[])])
    add('unfamiliar_ratify', 'The harbor assembly ratified the pilots\' compact after three readings, but deferred the dredging charter.', 'ratify',
        {'ratifier':'harbor assembly','instrument':'pilots\' compact'}, ['after three readings'], [
        ('Who ratified the pilots\' compact?',D,['harbor assembly'],['after three readings'],[]),
        ('Which body formally approved the pilots\' compact?',D,['harbor assembly'],['after three readings'],[]),
        ('What instrument did the assembly ratify?',D,['pilots\' compact'],['after three readings'],[]),
        ('Who ratified the dredging charter?',R,[],[],['harbor assembly']),
        ('Who ratified the compact and how many voted against it?',P,['harbor assembly'],['after three readings'],[])])
    add('bounded_narration', 'Authorized narration describes a dry fountain beside the copper stair. It names no builder.', 'describe',
        {'object':'dry fountain','landmark':'copper stair'}, [], [
        ('What stands beside the copper stair?',D,['dry fountain'],[],[]),
        ('Which landmark is next to the dry fountain?',D,['copper stair'],[],[]),
        ('Where is the dry fountain described?',D,['beside the copper stair'],[],[]),
        ('Who built the dry fountain?',R,[],[],[]),
        ('What stands beside the stair and who built it?',P,['dry fountain'],[],[])], provenance='bounded_expression')
    return rows


def digest(data):
    import json
    return sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
