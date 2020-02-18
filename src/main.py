'''
Copyright (c) 2013, ОАО "ТЕЛЕОФИС"

Разрешается повторное распространение и использование как в виде исходного кода, так и в двоичной форме, 
с изменениями или без, при соблюдении следующих условий:

- При повторном распространении исходного кода должно оставаться указанное выше уведомление об авторском праве, 
  этот список условий и последующий отказ от гарантий.
- При повторном распространении двоичного кода должна сохраняться указанная выше информация об авторском праве, 
  этот список условий и последующий отказ от гарантий в документации и/или в других материалах, поставляемых 
  при распространении.
- Ни название ОАО "ТЕЛЕОФИС", ни имена ее сотрудников не могут быть использованы в качестве поддержки или 
  продвижения продуктов, основанных на этом ПО без предварительного письменного разрешения.

ЭТА ПРОГРАММА ПРЕДОСТАВЛЕНА ВЛАДЕЛЬЦАМИ АВТОРСКИХ ПРАВ И/ИЛИ ДРУГИМИ СТОРОНАМИ «КАК ОНА ЕСТЬ» БЕЗ КАКОГО-ЛИБО 
ВИДА ГАРАНТИЙ, ВЫРАЖЕННЫХ ЯВНО ИЛИ ПОДРАЗУМЕВАЕМЫХ, ВКЛЮЧАЯ, НО НЕ ОГРАНИЧИВАЯСЬ ИМИ, ПОДРАЗУМЕВАЕМЫЕ ГАРАНТИИ 
КОММЕРЧЕСКОЙ ЦЕННОСТИ И ПРИГОДНОСТИ ДЛЯ КОНКРЕТНОЙ ЦЕЛИ. НИ В КОЕМ СЛУЧАЕ НИ ОДИН ВЛАДЕЛЕЦ АВТОРСКИХ ПРАВ И НИ 
ОДНО ДРУГОЕ ЛИЦО, КОТОРОЕ МОЖЕТ ИЗМЕНЯТЬ И/ИЛИ ПОВТОРНО РАСПРОСТРАНЯТЬ ПРОГРАММУ, КАК БЫЛО СКАЗАНО ВЫШЕ, НЕ 
НЕСЁТ ОТВЕТСТВЕННОСТИ, ВКЛЮЧАЯ ЛЮБЫЕ ОБЩИЕ, СЛУЧАЙНЫЕ, СПЕЦИАЛЬНЫЕ ИЛИ ПОСЛЕДОВАВШИЕ УБЫТКИ, ВСЛЕДСТВИЕ 
ИСПОЛЬЗОВАНИЯ ИЛИ НЕВОЗМОЖНОСТИ ИСПОЛЬЗОВАНИЯ ПРОГРАММЫ (ВКЛЮЧАЯ, НО НЕ ОГРАНИЧИВАЯСЬ ПОТЕРЕЙ ДАННЫХ, ИЛИ 
ДАННЫМИ, СТАВШИМИ НЕПРАВИЛЬНЫМИ, ИЛИ ПОТЕРЯМИ ПРИНЕСЕННЫМИ ИЗ-ЗА ВАС ИЛИ ТРЕТЬИХ ЛИЦ, ИЛИ ОТКАЗОМ ПРОГРАММЫ 
РАБОТАТЬ СОВМЕСТНО С ДРУГИМИ ПРОГРАММАМИ), ДАЖЕ ЕСЛИ ТАКОЙ ВЛАДЕЛЕЦ ИЛИ ДРУГОЕ ЛИЦО БЫЛИ ИЗВЕЩЕНЫ О 
ВОЗМОЖНОСТИ ТАКИХ УБЫТКОВ.
'''

import MOD
import GPIO
import gsm
import sms
import sms_prot
import sms_msg
import command
import config

#
# Defines
#
CFG = config.Config()

#
# Variables
#
OUT1_OFF_TIME = 0;
OUT1_STATE = 0
IN1_STATE = 0

def executeCommand(command):
    global OUT1_STATE
    global OUT1_OFF_TIME
    ok = 0
    if(command.getCommand() == 'OUT1'):
        if(command.getParameter() == '0'):
            GPIO.setIOvalue(6, 0)
            OUT1_STATE = 0
            ok = 1
        if(command.getParameter() == '1'):
            GPIO.setIOvalue(6, 1)
            OUT1_STATE = 1
            OUT1_OFF_TIME = MOD.secCounter() + int(CFG.get('OUT1TIME'))
            ok = 1
        print ('Set OUT1 to %s\r' % (command.getParameter()))
    elif(command.getCommand() == 'PASS'):
        CFG.set('PASS', command.getParameter())
        CFG.write()
        print ('PASS is set to: %s\r' % (command.getParameter()))
        ok = 1
    elif(command.getCommand() == 'IN1ONTXT'):
        CFG.set('IN1ONTXT', command.getParameter())
        CFG.write()
        print ('IN1ONTXT is set to: %s\r' % (command.getParameter()))
        ok = 1
    elif(command.getCommand() == 'IN1OFFTXT'):
        CFG.set('IN1OFFTXT', command.getParameter())
        CFG.write()
        print ('IN1OFFTXT is set to: %s\r' % (command.getParameter()))
        ok = 1
    elif(command.getCommand() == 'OUT1TIME'):
        CFG.set('OUT1TIME', command.getParameter())
        CFG.write()
        print ('OUT1TIME is set to: %s\r' % (command.getParameter()))
        ok = 1
    elif(command.getCommand() == 'ALERT'):
        CFG.set('ALERT', command.getParameter())
        CFG.write()
        print ('ALERT is set to: %s\r' % (command.getParameter()))
        ok = 1
    elif(command.getCommand() == 'SMSDELETEALL'):
        CFG.set('SMSDELETEALL', command.getParameter())
        CFG.write()
        print ('SMSDELETEALL is set to: %s\r' % (command.getParameter()))
        ok = 1
    if(ok == 1):
        return 'COMMAND %s OK;' % (command.getCommand())
    else:
        return 'COMMAND %s WRONG;' % (command.getCommand())

def sendAlert(text):
    for num in CFG.getList('ALERT'):
        print ('Send alert to: %s\r' % (num))
        sms.sendSms(sms_msg.SmsMessage('0', num, '', text))

def initInputs():
    GPIO.setIOdir(4, 0, 0) # Input 1
    GPIO.setIOdir(6, 0, 1) # Output 1
    global IN1_STATE
    IN1_STATE = GPIO.getIOvalue(4)

def ioProcessing():
    if((int(CFG.get('OUT1TIME')) > 0) and (MOD.secCounter() > OUT1_OFF_TIME) and (OUT1_STATE == 1)):
        executeCommand(command.Command('OUT1', '0'))
    global IN1_STATE
    IN1_STATE_NEW = GPIO.getIOvalue(4)
    if(IN1_STATE_NEW != IN1_STATE):
        if(IN1_STATE_NEW == 1):
            sendAlert(CFG.get('IN1ONTXT'))
        else:
            sendAlert(CFG.get('IN1OFFTXT'))
    IN1_STATE = IN1_STATE_NEW

def smsProcessing():
    message = sms.receiveSms()
    if message is not None:
        commands = sms_prot.parseCommand(CFG.get('PASS'), message.getText())
        if(len(commands) > 0):
            if(commands[0].getCommand() == 'WRONG_PASSWORD'):
                print ('Wrong password')
            else:
                result = ''
                for c in commands:
                    result = result + executeCommand(c)
                sms.sendSms(sms_msg.SmsMessage('0', message.getNumber(), '', result))
                if(CFG.get('SMSDELETEALL') == '0'):
                    sms.deleteSms(message.getId())
        if(CFG.get('SMSDELETEALL') == '1'):
            sms.deleteSms(message.getId())

def resetWatchdog():
    gsm.sendAT("AT#ENHRST=1,10", "OK", 5)

if __name__ == "__main__":
    try:
        CFG.read()
        print ('Start GSM init\r')
        gsm.init()
        print ('Start SMS init\r')
        sms.init()
        print ('IO init\r')
        initInputs()
        print ('Start main loop\r')
        while(1):
            resetWatchdog()
            smsProcessing()
            ioProcessing()
    except Exception, e:
        print ('Unhandled exception, reboot...\r')
        gsm.reboot()
        
        
