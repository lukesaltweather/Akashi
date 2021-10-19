--
-- PostgreSQL database dump
--

-- Dumped from database version 10.17 (Ubuntu 10.17-0ubuntu0.18.04.1)
-- Dumped by pg_dump version 10.17 (Ubuntu 10.17-0ubuntu0.18.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: chapters; Type: TABLE; Schema: public; Owner: Akashi
--

CREATE TABLE public.chapters (
    id integer NOT NULL,
    number double precision,
    title character varying,
    notes character varying,
    link_raw character varying,
    link_tl character varying,
    link_ts character varying,
    link_rd character varying,
    link_pr character varying,
    link_rl character varying,
    date_created timestamp without time zone,
    date_tl timestamp without time zone,
    date_rd timestamp without time zone,
    date_ts timestamp without time zone,
    date_pr timestamp without time zone,
    date_qcts timestamp without time zone,
    date_release timestamp without time zone,
    typesetter_id integer,
    translator_id integer,
    redrawer_id integer,
    proofreader_id integer,
    project_id integer
);


ALTER TABLE public.chapters OWNER TO "Akashi";

--
-- Name: chapters_id_seq; Type: SEQUENCE; Schema: public; Owner: Akashi
--

CREATE SEQUENCE public.chapters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.chapters_id_seq OWNER TO "Akashi";

--
-- Name: chapters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Akashi
--

ALTER SEQUENCE public.chapters_id_seq OWNED BY public.chapters.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: Akashi
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    title character varying NOT NULL,
    status character varying,
    link character varying,
    "altNames" character varying,
    typesetter_id integer,
    redrawer_id integer,
    translator_id integer,
    proofreader_id integer,
    thumbnail character varying(255),
    icon character varying(255),
    "position" integer,
    color character varying
);


ALTER TABLE public.projects OWNER TO "Akashi";

--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: Akashi
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_id_seq OWNER TO "Akashi";

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Akashi
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: staff; Type: TABLE; Schema: public; Owner: Akashi
--

CREATE TABLE public.staff (
    id integer NOT NULL,
    name character varying,
    discord_id bigint,
    status character varying
);


ALTER TABLE public.staff OWNER TO "Akashi";

--
-- Name: staff_id_seq; Type: SEQUENCE; Schema: public; Owner: Akashi
--

CREATE SEQUENCE public.staff_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.staff_id_seq OWNER TO "Akashi";

--
-- Name: staff_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Akashi
--

ALTER SEQUENCE public.staff_id_seq OWNED BY public.staff.id;


--
-- Name: chapters id; Type: DEFAULT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.chapters ALTER COLUMN id SET DEFAULT nextval('public.chapters_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: staff id; Type: DEFAULT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.staff ALTER COLUMN id SET DEFAULT nextval('public.staff_id_seq'::regclass);


--
-- Name: chapters chapters_pkey; Type: CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.chapters
    ADD CONSTRAINT chapters_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: staff staff_pkey; Type: CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_pkey PRIMARY KEY (id);


--
-- Name: chapters uq_number_project_id; Type: CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.chapters
    ADD CONSTRAINT uq_number_project_id UNIQUE (number, project_id);


--
-- Name: chapters chapters_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.chapters
    ADD CONSTRAINT chapters_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: chapters chapters_proofreader_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.chapters
    ADD CONSTRAINT chapters_proofreader_id_fkey FOREIGN KEY (proofreader_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: chapters chapters_redrawer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.chapters
    ADD CONSTRAINT chapters_redrawer_id_fkey FOREIGN KEY (redrawer_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: chapters chapters_translator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.chapters
    ADD CONSTRAINT chapters_translator_id_fkey FOREIGN KEY (translator_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: chapters chapters_typesetter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.chapters
    ADD CONSTRAINT chapters_typesetter_id_fkey FOREIGN KEY (typesetter_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: projects projects_proofreader_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_proofreader_id_fkey FOREIGN KEY (proofreader_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: projects projects_redrawer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_redrawer_id_fkey FOREIGN KEY (redrawer_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: projects projects_translator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_translator_id_fkey FOREIGN KEY (translator_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: projects projects_typesetter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Akashi
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_typesetter_id_fkey FOREIGN KEY (typesetter_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

