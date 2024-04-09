from typing import Type

from polyfactory import BaseFactory

from litestar import Controller, Litestar
from litestar._openapi.typescript_converter.converter import (
    convert_openapi_to_typescript,
)


def test_openapi_to_typescript_converter(person_controller: Type[Controller], pet_controller: Type[Controller]) -> None:
    BaseFactory.seed_random(1)
    app = Litestar(route_handlers=[person_controller, pet_controller])
    assert app.openapi_schema

    result = convert_openapi_to_typescript(openapi_schema=app.openapi_schema)
    assert (
        result.write()
        == """export namespace API {
	export namespace PetOwnerOrPetGetPetsOrOwners {
	export namespace Http200 {
	export type ResponseBody = ({
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
} | {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
})[];

	export interface ResponseHeaders {
	"x-my-tag"?: string;
};
};

	export namespace Http406 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};
};

	export namespace PetPets {
	export namespace Http200 {
	export type ResponseBody = {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
};
};

	export namespace ServiceIdPersonBulkBulkCreatePerson {
	export interface HeaderParameters {
	secret: string;
};

	export namespace Http201 {
	export type ResponseBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional: null | string;
	pets: null | {
	age: number;
	name: string;
	species: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
}[];
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	service_id: number;
};

	export type RequestBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional: null | string;
	pets: null | {
	age: number;
	name: string;
	species: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
}[];
};

	export namespace ServiceIdPersonBulkBulkPartialUpdatePerson {
	export interface HeaderParameters {
	secret: string;
};

	export namespace Http200 {
	export type ResponseBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional: null | string;
	pets: null | {
	age: number;
	name: string;
	species: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
}[];
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	service_id: number;
};

	export type RequestBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional: null | string;
	pets: null | {
	age: number;
	name: string;
	species: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
}[];
};

	export namespace ServiceIdPersonBulkBulkUpdatePerson {
	export interface HeaderParameters {
	secret: string;
};

	export namespace Http200 {
	export type ResponseBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
}[];
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	service_id: number;
};

	export type RequestBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
}[];
};

	export namespace ServiceIdPersonCreatePerson {
	export interface HeaderParameters {
	secret: string;
};

	export namespace Http201 {
	export type ResponseBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
};
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	service_id: number;
};

	export type RequestBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
};
};

	export namespace ServiceIdPersonDataclassGetPersonDataclass {
	export namespace Http200 {
	export type ResponseBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
};
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	service_id: number;
};
};

	export namespace ServiceIdPersonGetPersons {
	export interface CookieParameters {
	value: number;
};

	export interface HeaderParameters {
	secret: string;
};

	export namespace Http200 {
	export type ResponseBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
}[];
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	service_id: number;
};

	export interface QueryParameters {
	from_date?: null | number | string | string;
	gender?: "A" | "F" | "M" | "O" | ("A" | "F" | "M" | "O")[] | null;
	name?: null | string | string[];
	page: number;
	pageSize: number;
	to_date?: null | number | string | string;
};
};

	export namespace ServiceIdPersonPersonIdDeletePerson {
	export namespace Http204 {
	export type ResponseBody = undefined;
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	person_id: string;
	service_id: number;
};
};

	export namespace ServiceIdPersonPersonIdGetPersonById {
	export namespace Http200 {
	export type ResponseBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
};
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	person_id: string;
	service_id: number;
};
};

	export namespace ServiceIdPersonPersonIdPartialUpdatePerson {
	export namespace Http200 {
	export type ResponseBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional: null | string;
	pets: null | {
	age: number;
	name: string;
	species: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
};
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	person_id: string;
	service_id: number;
};

	export type RequestBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional: null | string;
	pets: null | {
	age: number;
	name: string;
	species: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
};
};

	export namespace ServiceIdPersonPersonIdUpdatePerson {
	export namespace Http200 {
	export type ResponseBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
};
};

	export namespace Http400 {
	export type ResponseBody = {
	detail: string;
	extra?: Record<string, unknown> | null | unknown[];
	status_code: number;
};
};

	export interface PathParameters {
	person_id: string;
	service_id: number;
};

	export type RequestBody = {
	complex: {
	
};
	first_name: string;
	id: string;
	last_name: string;
	optional?: null | string;
	pets?: null | {
	age: number;
	name: string;
	species?: "Cat" | "Dog" | "Monkey" | "Pig";
}[];
};
};
};"""
    )
