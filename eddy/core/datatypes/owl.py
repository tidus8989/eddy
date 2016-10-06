# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from enum import unique

from eddy.core.datatypes.common import Enum_


@unique
class Datatype(Enum_):
    """
    Extends Enum providing all the available datatypes.
    """
    rational = 'owl:rational'
    real = 'owl:real'
    PlainLiteral = 'rdf:PlainLiteral'
    XMLLiteral = 'rdf:XMLLiteral'
    Literal = 'rdfs:Literal'
    anyURI = 'xsd:anyURI'
    base64Binary = 'xsd:base64Binary'
    boolean = 'xsd:boolean'
    byte = 'xsd:byte'
    dateTime = 'xsd:dateTime'
    dateTimeStamp = 'xsd:dateTimeStamp'
    decimal = 'xsd:decimal'
    double = 'xsd:double'
    float = 'xsd:float'
    hexBinary = 'xsd:hexBinary'
    int = 'xsd:int'
    integer = 'xsd:integer'
    language = 'xsd:language'
    long = 'xsd:long'
    Name = 'xsd:Name'
    NCName = 'xsd:NCName'
    negativeInteger = 'xsd:negativeInteger'
    NMTOKEN = 'xsd:NMTOKEN'
    nonNegativeInteger = 'xsd:nonNegativeInteger'
    nonPositiveInteger = 'xsd:nonPositiveInteger'
    normalizedString = 'xsd:normalizedString'
    positiveInteger = 'xsd:positiveInteger'
    short = 'xsd:short'
    string = 'xsd:string'
    token = 'xsd:token'
    unsignedByte = 'xsd:unsignedByte'
    unsignedInt = 'xsd:unsignedInt'
    unsignedLong = 'xsd:unsignedLong'
    unsignedShort = 'xsd:unsignedShort'

    @classmethod
    def forProfile(cls, profile):
        """
        Returns the list of supported datatypes for the given OWL 2 profile.
        :type profile: OWLProfile
        :rtype: list
        """
        if profile is OWLProfile.OWL2:
            return [x for x in Datatype]
        elif profile is OWLProfile.OWL2QL:
            return [Datatype.rational, Datatype.real, Datatype.PlainLiteral, Datatype.XMLLiteral,
                Datatype.Literal, Datatype.anyURI, Datatype.base64Binary, Datatype.dateTime,
                Datatype.dateTimeStamp, Datatype.decimal, Datatype.hexBinary, Datatype.integer,
                Datatype.Name, Datatype.NCName, Datatype.NMTOKEN, Datatype.nonNegativeInteger,
                Datatype.normalizedString, Datatype.string, Datatype.token]
        raise ValueError('unsupported profile: %s' % profile)


@unique
class Facet(Enum_):
    """
    Extends Enum providing all the available Facet restrictions.
    """
    maxExclusive = 'xsd:maxExclusive'
    maxInclusive = 'xsd:maxInclusive'
    minExclusive = 'xsd:minExclusive'
    minInclusive = 'xsd:minInclusive'
    langRange = 'rdf:langRange'
    length = 'xsd:length'
    maxLength = 'xsd:maxLength'
    minLength = 'xsd:minLength'
    pattern = 'xsd:pattern'

    @classmethod
    def forDatatype(cls, value):
        """
        Returns a collection of Facets for the given datatype
        :type value: Datatype
        :rtype: list
        """
        allvalues = [x for x in cls]
        numbers = [Facet.maxExclusive, Facet.maxInclusive, Facet.minExclusive, Facet.minInclusive]
        strings = [Facet.langRange, Facet.length, Facet.maxLength, Facet.minLength, Facet.pattern]
        binary = [Facet.length, Facet.maxLength, Facet.minLength]
        anyuri = [Facet.length, Facet.maxLength, Facet.minLength, Facet.pattern]

        return {
            Datatype.anyURI: anyuri,
            Datatype.base64Binary: binary,
            Datatype.boolean: [],
            Datatype.byte: numbers,
            Datatype.dateTime: numbers,
            Datatype.dateTimeStamp: numbers,
            Datatype.decimal: numbers,
            Datatype.double: numbers,
            Datatype.float: numbers,
            Datatype.hexBinary: binary,
            Datatype.int: numbers,
            Datatype.integer: numbers,
            Datatype.language: strings,
            Datatype.Literal: allvalues,
            Datatype.long: numbers,
            Datatype.Name: strings,
            Datatype.NCName: strings,
            Datatype.negativeInteger: numbers,
            Datatype.NMTOKEN: strings,
            Datatype.nonNegativeInteger: numbers,
            Datatype.nonPositiveInteger: numbers,
            Datatype.normalizedString: strings,
            Datatype.PlainLiteral: strings,
            Datatype.positiveInteger: numbers,
            Datatype.rational: numbers,
            Datatype.real: numbers,
            Datatype.short: numbers,
            Datatype.string: strings,
            Datatype.token: strings,
            Datatype.unsignedByte: numbers,
            Datatype.unsignedInt: numbers,
            Datatype.unsignedLong: numbers,
            Datatype.unsignedShort: numbers,
            Datatype.XMLLiteral: []
        }[value]


@unique
class OWLAxiom(Enum_):
    """
    Extends Enum providing the set of supported OWL Axiom.
    """
    Annotation = 'Annotation'
    AsymmetricObjectProperty = 'AsymmetricObjectProperty'
    ClassAssertion = 'ClassAssertion'
    DataPropertyAssertion = 'DataPropertyAssertion'
    DataPropertyDomain = 'DataPropertyDomain'
    DataPropertyRange = 'DataPropertyRange'
    Declaration = 'Declaration'
    DisjointClasses = 'DisjointClasses'
    DisjointDataProperties = 'DisjointDataProperties'
    DisjointObjectProperties = 'DisjointObjectProperties'
    EquivalentClasses = 'EquivalentClasses'
    EquivalentDataProperties = 'EquivalentDataProperties'
    EquivalentObjectProperties = 'EquivalentObjectProperties'
    FunctionalDataProperty = 'FunctionalDataProperty'
    FunctionalObjectProperty = 'FunctionalObjectProperty'
    InverseFunctionalObjectProperty = 'InverseFunctionalObjectProperty'
    InverseObjectProperties = 'InverseObjectProperties'
    IrreflexiveObjectProperty = 'IrreflexiveObjectProperty'
    NegativeDataPropertyAssertion = 'NegativeDataPropertyAssertion'
    NegativeObjectPropertyAssertion = 'NegativeObjectPropertyAssertion'
    ObjectPropertyAssertion = 'ObjectPropertyAssertion'
    ObjectPropertyDomain = 'ObjectPropertyDomain'
    ObjectPropertyRange = 'ObjectPropertyRange'
    ReflexiveObjectProperty = 'ReflexiveObjectProperty'
    SubClassOf = 'SubClassOf'
    SubDataPropertyOf = 'SubDataPropertyOf'
    SubObjectPropertyOf = 'SubObjectPropertyOf'
    SymmetricObjectProperty = 'SymmetricObjectProperty'
    TransitiveObjectProperty = 'TransitiveObjectProperty'


@unique
class OWLProfile(Enum_):
    """
    Extends Enum providing all the available OWL 2 profiles.
    """
    OWL2 = 'OWL 2'
    OWL2EL = 'OWL 2 EL'
    OWL2QL = 'OWL 2 QL'
    OWL2RL = 'OWL 2 RL'


@unique
class OWLSyntax(Enum_):
    """
    Extends Enum providing all the available OWL 2 syntax for ontology serialization.
    """
    Functional = 'Functional-style syntax'
    Manchester = 'Manchester OWL syntax'
    RDF = 'RDF/XML syntax for OWL'
    Turtle = 'Turtle syntax'