"""Bounded transforms of native script globals and legacy-byte journal text."""
import struct
from native_format import Reader

def uint(value):return struct.pack('<I',value)

def string(value):
    data=value.encode('latin1')
    return uint(len(data))+data

def restore_globals(data,original):
    expected=dict(original)
    if len(expected)!=len(original):raise ValueError('Duplicate source global names')
    r=Reader(data);count=r.u();out=bytearray(uint(count));seen=set();changed=0
    for _ in range(count):
        start=r.p;typ=r.u()
        if typ in (1,2,3):
            name=r.s().decode('latin1');size=r.u();value_start=r.p
            if typ in (1,2):r.skip(size*4)
            else:
                for __ in range(size):r.s()
            record=bytearray(data[start:r.p])
            if name in expected:
                if typ!=2:raise ValueError('Source integer global has incompatible native type: '+name)
                values=expected[name]
                if len(values)!=size:raise ValueError('Global array length mismatch: '+name)
                if name in seen:raise ValueError('Duplicate native global: '+name)
                seen.add(name)
                patch=b''.join(struct.pack('<i',value) for value in values)
                if data[value_start:r.p]!=patch:changed+=1
                record[value_start-start:]=patch
            out+=record
        elif typ==7:
            cls=r.number('<B')
            if cls not in (0,1,2,3):raise ValueError('Unknown native instance class')
            if cls:
                r.s();r.skip(4)
                if cls==3:r.skip(4)
            out+=data[start:r.p]
        elif typ==0:out+=data[start:r.p]
        else:raise ValueError('Unsupported native global record type: '+str(typ))
    r.end()
    if seen!=set(expected):raise ValueError('Source globals missing from native save: '+str(len(set(expected)-seen)))
    return bytes(out),dict(originalGlobalsVerified=len(seen),globalsRestoredAfterWorldInitialization=changed)

def journal_tail_offset(data):
    r=Reader(data)
    for _ in range(r.u()):
        r.s();r.skip(2)
        for __ in range(r.u()):r.s()
    return r.p

def restore_journal(data,original):
    tail=data[journal_tail_offset(data):]
    out=bytearray(uint(len(original)))
    for quest in original:
        out+=string(quest['title'])+bytes([quest['section'],quest['status']])+uint(len(quest['entries']))
        for entry in reversed(quest['entries']):out+=string(entry)
    return bytes(out)+tail


def guild_table_offset(data,native_size=66):
    r=Reader(data,journal_tail_offset(data))
    r.skip(r.u()*8)
    if r.u()!=native_size*native_size:raise ValueError('Unsupported native guild-table size')
    offset=r.p;r.skip(native_size*native_size*4);r.end()
    return offset


def restore_guild_table(data,original,source_size=42,native_size=66):
    if not 0<source_size<=native_size:raise ValueError('Invalid guild-table dimensions')
    if len(original)!=source_size*source_size:raise ValueError('Invalid source guild-table size')
    offset=guild_table_offset(data,native_size)
    result=bytearray(data)
    for row in range(source_size):
        for col in range(source_size):
            struct.pack_into('<i',result,offset+(row*native_size+col)*4,original[row*source_size+col])
    return bytes(result)
