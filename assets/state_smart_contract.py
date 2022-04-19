from pyteal import *
var_creator = Bytes("root")
def DCR_program():
    is_creator = Txn.sender() == App.globalGet(var_creator)
    init__=Seq([
        App.globalPut(var_creator, Txn.sender()),
        App.globalPut(Bytes("marking"),Bytes("base16", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")), #A:00000: excluded; B:00001: included; 0001x:pending; 001xx:executed     If it is executed, its condition constrants to others are removed. If it is pending, its milestone constraints to others are kept.
        App.globalPut(total_events,Int(0)),
        Return(Int(1))
    ])
    total_events=ScratchVar(TealType.uint64)
    total_ops=ScratchVar(TealType.uint64)
    k=ScratchVar(TealType.uint64)
    #add_event(sender,executor)
    add_event = Seq([
        Assert(is_creator),
        total_events.store(App.globalGet(Bytes("total_events"))),
        Assert(total_events.load()<=Int(61)),
        total_events.store(total_events.load()+Int(1)),
        App.globalPut(Bytes("total_events"),total_events.load()),
        total_ops.store((total_events.load()-Int(1))*Int(2)+Int(3)+Int(1)),
        If (total_ops.load()>Int(64))
        .Then(App.localPut(Txn.accounts[(total_ops.load()-Int(64)) / Int(16) -Int(1)],Itob(total_events.load()),Bytes(Txn.application_args[1]))) # Key: event_id; Value:executor's address
        .Else(App.globalPut(Itob(total_events.load()),Bytes(Txn.application_args[1]))),# Key: event_id; Value:executor's address
        total_ops.store(total_ops.load()+Int(1)),
        If (total_ops.load()>Int(64))
        .Then(App.localPut(Txn.accounts[total_ops.load()  / Int(16) -Int(1)],Itob(total_events.load())+Int(300), Bytes("base32", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"))) # Key: event_id_; Value:the links to others
        .Else(App.globalPut(Itob(total_events.load())+Int(300), Bytes("base32", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"))),
        Return(Int(1))
    ])

    

    event_1=ScratchVar(TealType.uint64)
    event_2=ScratchVar(TealType.uint64)
    ops1=ScratchVar(TealType.uint64)
    ops2=ScratchVar(TealType.uint64)
    current_1_links=ScratchVar(TealType.bytes)
    current_2_links=ScratchVar(TealType.bytes)
    #add_relationship (sender,event1,event2,relationship)
    add_relationship = Seq([
        Assert(is_creator),
        event_1=Btoi(Txn.application_args[1]),
        event_2=Btoi(Txn.application_args[2]),
        #get the out-links of event1
        ops1.store((event_1.load()-Int(1))*Int(2)+Int(5)),# the first +1 is for executor identity, the second +1 is for the out links
        If (ops1.load()>Int(64))
        .Then(current_1_links.store(App.localGet(Txn.accounts[ops1.load() / Int(16) -Int(1)],Itob(event_1.load())+Int(300)  )))
        .Else(current_1_links.store(App.globalGet(Itob(event_1.load())+Int(300)))),

        ops2.store((event_2.load()-Int(1))*Int(2)+Int(5)),# the first +1 is for executor identity, the second +1 is for the out links
        If (ops2.load()>Int(64))
        .Then(current_2_links.store(App.localGet(Txn.accounts[ops1.load() / Int(16) -Int(1)],Itob(event_2.load())+Int(300)  )))
        .Else(current_2_links.store(App.globalGet(Itob(event_2.load())+Int(300)))),
        #Add the relationship
        If (Txn.application_args[3]==Bytes("Include"),k.store(Int(0))),
        If (Txn.application_args[3]==Bytes("Exclude"),k.store(Int(1))),
        If (Txn.application_args[3]==Bytes("Milestone"),k.store(Int(2))),
        If (Txn.application_args[3]==Bytes("Condition"),k.store(Int(3))),
        If (Txn.application_args[3]==Bytes("Response"),k.store(Int(4))),
        If (k.load()==Int(2),
        current_2_links.store(SetBit(Bytes("base32", current_2_links.load()), Int((event_1.load()-Int(1))*Int(5))+k.load(),Int(1)))
        ),
        If (k.load()==Int(3),
        current_2_links.store(SetBit(Bytes("base32", current_2_links.load()), Int((event_1.load()-Int(1))*Int(5))+k.load(),Int(1)))
        ),
        If (k.load()==Int(0),
        current_1_links.store(SetBit(Bytes("base32", current_1_links.load()), Int((event_2.load()-Int(1))*Int(5))+k.load(),Int(1)))
        ),
        If (k.load()==Int(1),
        current_1_links.store(SetBit(Bytes("base32", current_1_links.load()), Int((event_2.load()-Int(1))*Int(5))+k.load(),Int(1)))
        ),
        If (k.load()==Int(4),
        current_1_links.store(SetBit(Bytes("base32", current_1_links.load()), Int((event_2.load()-Int(1))*Int(5))+k.load(),Int(1)))
        ),
        #update the links
        If (ops1.load()>Int(64))
        .Then(App.localPut(Txn.accounts[ops1.load()/ Int(16) -Int(1)],Itob(event_1.load())+Int(300), Bytes("base32", current_1_links.load())))
        .Else(App.globalPut(Itob(event_1.load())+Int(300), Bytes("base32", current_1_links.load()))),
        If (ops2.load()>Int(64))
        .Then(App.localPut(Txn.accounts[ops2.load()/ Int(16) -Int(1)],Itob(event_2.load())+Int(300), Bytes("base32", current_2_links.load())))
        .Else(App.globalPut(Itob(event_1.load())+Int(300), Bytes("base32", current_2_links.load()))),
        Return(Int(1))
        ])

    # execute_event(sender,event_id)
     event_id=ScratchVar(TealType.uint64)
     executor=ScratchVar(TealType.bytes)
     mk=ScratchVar(TealType.bytes)
     _mk=ScratchVar(TealType.bytes)
     i = ScratchVar(TealType.uint64)
     id= ScratchVar(TealType.uint64)
     execute_event=Seq([
         event_id.store(Btoi(Txn.application_args[1])),
         #Get the executor
		 ops1.store((event_id.load()-Int(1))*Int(2)+Int(4)), #+1 is because each event has a executor and a string indiate its links to others, and the executor comes first.
         If (ops1.load()>Int(64))
         .Then(executor.store(App.localGet(Txn.accounts[ops1.load()/Int(64) -1],Itob(event_id.load()))))
         .Else(executor.store(App.globalGet(Itob(event_id)))),
         Assert(executor==Txn.sender()),
         mk.store(App.globalGet(Bytes("marking"))),
         Assert(GetBit(Bytes("base16", mk.load()),Int(((event_id.load()-Int(1))*Int(4))))==Int(1)),#the event must be included when executing
         #Determine if the event can be executed
		 ops1.store((event_id.load()-Int(1))*Int(2)+Int(5)), #+1 is because each event has a executor and a string indiate its links to others, and the executor comes first.
         If (ops1.load()>Int(64))
         .Then(_mk.store(App.localGet(Txn.accounts[ops1.load()/Int(64) -1],Itob(event_id.load()+Int(300)))))
         .Else(_mk.store(App.globalGet(Itob(event_id.load()+Int(300))))),
          For(i.store(Int(1)), i.load() <= App.globalGet(Bytes("total_events"))*Int(5), i.store(i.load() + Int(1))).Do(
                     id=Int(i/Int(5))+1,
                     If(i.load() % Int(5)==Int(2), #Milestone
                     If(GetBit(_mk.load(),(id.load()-Int(1))*Int(5)+Int(2))==Int(1), # The event (id) milestone the current event.
                     If(GetBit(Bytes("base16", mk.load()),Int(((id.load()-Int(1))*Int(4)))==Int(1),#event (id) is included
                        Assert(GetBit(Bytes("base16", mk.load()),Int(((id.load()-Int(1))*Int(4)+Int(1)))!=Int(1))))))), # The event can only be executed if the event (id) is included but not pending
                      If(i.load() % Int(5)==Int(3),#Condition
                      If(GetBit(_mk.load(),(id.load()-Int(1))*Int(5)+Int(3))==Int(1), # The event (id) condition the current event.
                      Assert(GetBit(Bytes("base16", mk.load()),Int(((id.load()-Int(1))*Int(4)+Int(2)))==Int(1)))) #The event can only be executed if the event (id) has executed.
                      )),
         mk.store(SetBit(mk.load(),(event_id.load()-1)*Int(4)+Int(1),Int(0))), #If the event is pending, the pending status should be cancelled after execution.
         mk.store(SetBit(mk.load(),(event_id.load()-1)*Int(4)+Int(2),Int(1))), #Update the status of the event as executed.
        #Update the status of other events
          For(i.store(Int(1)), i.load() <= App.globalGet(Bytes("total_events"))*Int(5), i.store(i.load() + Int(1))).Do(
            id=Int(i/Int(5))+1,
            If(i % Int(5)==Int(0),#include
            If(GetBit(Bytes("base32", _mk.load()),Int(((i.load()-Int(1))*Int(5))))==Int(1), #include
                mk.store(SetBit(mk.load(),(id.load()-Int(1))*Int(4),Int(1))))),# include the event (id)
            If(i % Int(5)==Int(1),#exclude
            If(GetBit(Bytes("base32", _mk.load()),Int(((i.load()-Int(1))*Int(5))))+Int(1)==Int(1), #exclude
                mk.store(SetBit(mk.load(),(id.load()-Int(1))*Int(4),Int(0)))) # exclude the event (id)
            ),
            If(i % 5==Int(4),# pend.
               If(GetBit(Bytes("base32", _mk.load()),Int(((i.load()-Int(1))*Int(5)))+Int(4))==Int(1), #pended
                 mk.store(SetBit(mk.load(),(id.load()-Int(1))*Int(4)+Int(1),Int(1))))),
            ),
	      App.globalPut(Bytes("marking"),mk),
     ])

     #include_event (sender,event)
     include_event= Seq([
      Assert(is_creator),
            App.globalPut(Bytes("marking"),SetBit(Bytes("base16", App.globalGet(Bytes("marking")), Int(((Btoi(Txn.application_args[2])-Int(1))*Int(4)),Int(1))))),
     ])

     #exclude_event (sender,event)
     exclude_event= Seq([
      Assert(is_creator),
            App.globalPut(Bytes("marking"),SetBit(Bytes("base16", App.globalGet(Bytes("marking")), Int(((Btoi(Txn.application_args[2])-Int(1))*Int(4)),Int(0)))),
     ])
     #pend_event (sender,event)
     pend_event= Seq([
      Assert(is_creator),
          App.globalPut(Bytes("marking"),SetBit(Bytes("base16", App.globalGet(Bytes("marking")), Int(((Btoi(Txn.application_args[2])-Int(1))*Int(4)+Int(1)),Int(1)))),
     ])
    program = Cond(
        [Txn.application_id() == Int(0), init__],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.OptIn, Return(Int(1))],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(1))],
        [Txn.application_args[0] == Bytes("add_event"), add_event],
        [Txn.application_args[0] == Bytes("execute_event"), execute_event],
        [Txn.application_args[0] == Bytes("add_relationship"), add_relationship],
        [Txn.application_args[0] == Bytes("pend_event"), pend_event],
        [Txn.application_args[0] == Bytes("exclude_event"), exclude_event],
        [Txn.application_args[0] == Bytes("include_event"), include_event]
    )
    return program

if __name__ == "__main__":
    print(compileTeal(DCR_program(), Mode.Application, version=5))